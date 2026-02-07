"""
MustDo Collector (DEPRECATED)

Crawls MustDo event listing pages, derives per-event iCal URLs, and stores
them as source_feeds for later ingestion.

This collector is no longer actively used, but is kept for reference.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

import app.core.env  # noqa: F401
from app.core.logging import setup_logging
from app.db import SessionLocal
from app.models.source import Source

from .utils import (
    add_common_args,
    add_feed_args,
    add_pagination_args,
    get_http_session,
    upsert_source_feed,
    validate_ical_url,
    write_test_data,
)

logger = logging.getLogger(__name__)

EVENT_PATH_RE = re.compile(r"^/events/[^/]+/?$")


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------


def canon_event_page(url: str) -> str:
    """Normalize to a trailing-slash canonical event page URL."""
    u = url.split("#", 1)[0].rstrip("/")
    return u + "/"


def derive_ical_url(event_page: str) -> str:
    """MustDo per-event iCal is typically ``<event-page>/ical/``."""
    return canon_event_page(event_page) + "ical/"


def make_external_id(event_page: str) -> str:
    path = urlparse(event_page).path.rstrip("/")
    slug = path.split("/")[-1]
    return f"mustdo:{slug}"


# ---------------------------------------------------------------------------
# Page parsing
# ---------------------------------------------------------------------------


def extract_event_pages(html: str, *, base_url: str) -> set[str]:
    """Extract event page URLs from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    found: set[str] = set()

    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue
        abs_url = urljoin(base_url, href)

        if urlparse(abs_url).netloc != urlparse(base_url).netloc:
            continue

        if EVENT_PATH_RE.match(urlparse(abs_url).path):
            found.add(canon_event_page(abs_url))

    logger.debug(
        "Extracted event pages",
        extra={"base_url": base_url, "events_found": len(found)},
    )
    return found


def find_next_page(html: str, *, base_url: str) -> str | None:
    """Find the next page URL via common WP pagination patterns."""
    soup = BeautifulSoup(html, "html.parser")

    a = soup.find("a", attrs={"rel": "next"})
    if a and a.get("href"):
        return urljoin(base_url, a["href"])

    a = soup.select_one("a.next, a.next.page-numbers, .pagination a.next")
    if a and a.get("href"):
        return urljoin(base_url, a["href"])

    for a in soup.select("a[href]"):
        txt = (a.get_text() or "").strip().lower()
        if txt in {"next", "next »", "older posts"}:
            return urljoin(base_url, a["href"])

    return None


# ---------------------------------------------------------------------------
# Core collector
# ---------------------------------------------------------------------------


def run_collector(
    db: Session,
    source: Source,
    *,
    max_pages: int = 10,
    delay: float = 1.0,
    validate_ical: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Run the MustDo collector.

    Callable from both CLI and Celery tasks.
    """
    from .utils import fetch_html

    if not source.url:
        raise SystemExit("Source.url is empty")

    logger.info(
        "Starting MustDo collector",
        extra={
            "source_id": source.id,
            "max_pages": max_pages,
            "delay": delay,
            "dry_run": dry_run,
            "validate_ical": validate_ical,
        },
    )

    stats: dict[str, Any] = {
        "source_id": source.id,
        "pages_crawled": 0,
        "events_found": 0,
        "events_upserted": 0,
        "ical_validated": 0,
        "ical_invalid": 0,
        "errors": 0,
    }

    session = get_http_session(
        headers={"Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"},
    )

    # Phase 1: Crawl listing pages
    page_url: str | None = source.url
    all_events: set[str] = set()

    while page_url and stats["pages_crawled"] < max_pages:
        stats["pages_crawled"] += 1
        logger.info(
            "Crawling page",
            extra={
                "source_id": source.id,
                "page_number": stats["pages_crawled"],
                "page_url": page_url,
            },
        )

        try:
            html = fetch_html(session, page_url, timeout=25)
            events = extract_event_pages(html, base_url=page_url)
            stats["events_found"] += len(events)
            all_events |= events

            page_url = find_next_page(html, base_url=page_url)
            time.sleep(delay)
        except Exception as e:
            stats["errors"] += 1
            logger.error(
                "Error crawling page",
                extra={
                    "source_id": source.id,
                    "page_number": stats["pages_crawled"],
                    "page_url": page_url,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )
            page_url = None

    logger.info(
        "Crawling complete",
        extra={
            "source_id": source.id,
            "pages_crawled": stats["pages_crawled"],
            "total_unique_events": len(all_events),
        },
    )

    if not all_events:
        logger.warning("No events found", extra={"source_id": source.id})
        stats["status"] = "success"
        return stats

    # Phase 2: Upsert source feeds
    dry_run_items: list[dict[str, Any]] = []

    for i, event_page in enumerate(sorted(all_events), start=1):
        try:
            ical_url = derive_ical_url(event_page)

            if validate_ical:
                if validate_ical_url(ical_url, session):
                    stats["ical_validated"] += 1
                else:
                    stats["ical_invalid"] += 1
                    logger.warning(
                        "iCal URL validation failed, skipping",
                        extra={
                            "source_id": source.id,
                            "event_page": event_page,
                            "ical_url": ical_url,
                        },
                    )
                    continue

            external_id = make_external_id(event_page)

            upsert_source_feed(
                db,
                source_id=source.id,
                external_id=external_id,
                page_url=event_page,
                ical_url=ical_url,
                dry_run=dry_run,
            )
            stats["events_upserted"] += 1

            if dry_run:
                dry_run_items.append(
                    {
                        "external_id": external_id,
                        "event_page": event_page,
                        "ical_url": ical_url,
                    }
                )

            if i % 25 == 0:
                logger.info(
                    "Upsert progress",
                    extra={
                        "source_id": source.id,
                        "upserted": i,
                        "total": len(all_events),
                    },
                )
        except Exception as e:
            stats["errors"] += 1
            logger.error(
                "Error upserting item",
                extra={
                    "source_id": source.id,
                    "event_page": event_page,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )

    if not dry_run:
        db.commit()
        logger.info("Database commit successful", extra={"source_id": source.id})
    else:
        write_test_data(
            "mustdo",
            {
                "source_id": source.id,
                "source_name": source.name,
                "collected_at": datetime.now(UTC).isoformat(),
                "items": dry_run_items,
            },
        )

    stats["status"] = "success"
    logger.info("MustDo collector completed", extra=stats)

    return stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    setup_logging()

    parser = argparse.ArgumentParser(
        description="Collect MustDo events source and populate source_feeds table (DEPRECATED)"
    )
    add_common_args(parser, default_delay=1.0)
    add_pagination_args(parser)
    add_feed_args(parser)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        source = db.get(Source, args.source_id)
        if not source:
            logger.error("Source not found", extra={"source_id": args.source_id})
            raise SystemExit(f"Source {args.source_id} not found")

        run_collector(
            db,
            source,
            max_pages=args.max_pages,
            delay=args.delay,
            validate_ical=args.validate_ical,
            dry_run=args.dry_run,
        )

    except Exception as e:
        db.rollback()
        logger.critical(
            "Fatal error in collector",
            extra={
                "source_id": args.source_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
