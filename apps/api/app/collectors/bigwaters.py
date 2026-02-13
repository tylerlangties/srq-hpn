"""
Big Waters Land Trust collector.

Fetches events from the WordPress REST API, visits each event detail page
for location/time data, and writes events + occurrences directly to the
database.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

import app.core.env  # noqa: F401
from app.core.logging import setup_logging
from app.db import SessionLocal
from app.models.source import Source
from app.services.ingest_upsert import upsert_event_and_occurrence

from .utils import (
    add_common_args,
    add_feed_args,
    add_pagination_args,
    get_http_session,
    write_test_data,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://bigwaterslandtrust.org"
EVENTS_API_URL = f"{BASE_URL}/wp-json/wp/v2/event"

EASTERN_TZ = ZoneInfo("America/New_York")

# Matches closure / non-event titles like "PARK CLOSED Public Holiday"
SKIP_TITLE_RE = re.compile(r"\bpark\s+closed\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class CollectedEvent:
    event_id: int
    slug: str
    title: str
    description: str | None
    start_utc: datetime
    end_utc: datetime | None
    location: str | None
    event_url: str


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def make_external_id(event_id: int) -> str:
    return f"bigwaters:{event_id}"


def clean_text(value: str | None) -> str | None:
    if not value:
        return None
    text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    if not text:
        return None
    return text[:2000]


def parse_event_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            logger.warning("Unable to parse event datetime", extra={"value": text})
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=EASTERN_TZ)

    return parsed.astimezone(UTC)


def build_location(name: str | None, address: str | None) -> str | None:
    name = (name or "").strip()
    address = (address or "").strip()
    if name and address:
        if name.lower() in address.lower():
            return address
        return f"{name}, {address}"
    if address:
        return address
    if name:
        return name
    return None


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------


def fetch_events_page(
    session, *, page: int, per_page: int = 100
) -> tuple[list[dict[str, Any]], int]:
    params = {"page": page, "per_page": per_page}
    resp = session.get(EVENTS_API_URL, params=params, timeout=30)
    resp.raise_for_status()
    total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
    return resp.json(), total_pages


def fetch_all_events(
    session, *, max_pages: int = 10, delay: float = 0.5
) -> list[dict[str, Any]]:
    all_events: list[dict[str, Any]] = []
    page = 1
    total_pages = 1

    while page <= max_pages and page <= total_pages:
        events, total_pages = fetch_events_page(session, page=page)
        if not events:
            break
        all_events.extend(events)
        logger.info(
            "Fetched events page",
            extra={
                "page": page,
                "events_on_page": len(events),
                "total_pages": total_pages,
            },
        )
        page += 1
        if page <= total_pages:
            time.sleep(delay)

    return all_events


def extract_location_from_page(soup: BeautifulSoup) -> str | None:
    name = None
    address = None

    heading = soup.find(
        lambda tag: tag.name in {"h2", "h3", "h4"}
        and tag.get_text(strip=True).lower() == "location"
    )
    if heading:
        next_heading = heading.find_next("h4")
        if next_heading:
            name = next_heading.get_text(" ", strip=True)

    address_elem = soup.select_one(".location-address p")
    if address_elem:
        address = address_elem.get_text(" ", strip=True)

    if not address:
        marker_heading = soup.select_one(".acf-map .marker h4")
        if marker_heading:
            address = marker_heading.get_text(" ", strip=True)

    return build_location(name, address)


def extract_description_from_page(soup: BeautifulSoup) -> str | None:
    content = soup.select_one(".entry-content")
    if content:
        text = content.get_text(" ", strip=True)
        if text:
            return text[:2000]

    meta_desc = soup.find("meta", attrs={"property": "og:description"})
    if meta_desc:
        content_value = meta_desc.get("content")
        if content_value:
            text = str(content_value).strip()
            if text:
                return text[:2000]

    return None


def collect_event_detail(session, url: str) -> dict[str, Any] | None:
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    date_elem = soup.select_one(".pc-event-time")
    start_utc = parse_event_datetime(
        date_elem.get_text(strip=True) if date_elem else None
    )
    if not start_utc:
        logger.warning("Missing event start datetime", extra={"url": url})
        return None

    location = extract_location_from_page(soup)
    description = extract_description_from_page(soup)

    return {
        "start_utc": start_utc,
        "end_utc": None,
        "location": location,
        "description": description,
    }


def build_collected_event(
    event: dict[str, Any], detail: dict[str, Any]
) -> CollectedEvent | None:
    event_id = event.get("id")
    if not event_id:
        return None

    slug = (event.get("slug") or "").strip() or str(event_id)
    title = (
        clean_text(event.get("title", {}).get("rendered"))
        or slug.replace("-", " ").title()
    )

    description = clean_text(event.get("content", {}).get("rendered"))
    if not description:
        description = detail.get("description")

    event_url = event.get("link") or f"{BASE_URL}/events/"

    return CollectedEvent(
        event_id=event_id,
        slug=slug,
        title=title,
        description=description,
        start_utc=detail["start_utc"],
        end_utc=detail.get("end_utc"),
        location=detail.get("location"),
        event_url=event_url,
    )


# ---------------------------------------------------------------------------
# Ingestion helper
# ---------------------------------------------------------------------------


def ingest_event(
    db: Session, *, source: Source, event: CollectedEvent, dry_run: bool = False
) -> None:
    external_id = make_external_id(event.event_id)

    if dry_run:
        return

    upsert_event_and_occurrence(
        db,
        source=source,
        external_id=external_id,
        title=event.title,
        description=event.description,
        location=event.location,
        start_utc=event.start_utc,
        end_utc=event.end_utc,
        external_url=event.event_url,
        fallback_external_url=None,
    )


def _serialize_event(event: CollectedEvent) -> dict[str, Any]:
    return {
        "external_id": make_external_id(event.event_id),
        "event_id": event.event_id,
        "slug": event.slug,
        "title": event.title,
        "description": event.description,
        "start_utc": event.start_utc.isoformat(),
        "end_utc": event.end_utc.isoformat() if event.end_utc else None,
        "location": event.location,
        "event_url": event.event_url,
    }


# ---------------------------------------------------------------------------
# Core collector
# ---------------------------------------------------------------------------


def run_collector(
    db: Session,
    source: Source,
    *,
    delay: float = 0.5,
    max_pages: int = 10,
    include_past: bool = False,
    future_only: bool | None = None,
    validate_ical: bool = False,
    categories: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Run the Big Waters Land Trust collector.

    Callable from both CLI and Celery tasks.
    """
    effective_future_only = not include_past if future_only is None else future_only

    logger.info(
        "Starting Big Waters collector",
        extra={
            "source_id": source.id,
            "dry_run": dry_run,
            "delay": delay,
            "max_pages": max_pages,
            "include_past": include_past,
            "future_only": effective_future_only,
            "validate_ical": validate_ical,
            "categories": categories,
        },
    )

    if validate_ical or categories:
        logger.info(
            "Some feed-oriented flags are accepted but not used by this collector",
            extra={
                "source_id": source.id,
                "validate_ical": validate_ical,
                "categories": categories,
            },
        )

    stats: dict[str, Any] = {
        "source_id": source.id,
        "events_discovered": 0,
        "events_collected": 0,
        "events_failed": 0,
        "events_skipped_closed": 0,
        "events_skipped_past": 0,
        "occurrences_upserted": 0,
        "errors": 0,
    }

    session = get_http_session(
        headers={"Accept": "application/json,text/html;q=0.9,*/*;q=0.8"},
    )

    events = fetch_all_events(session, max_pages=max_pages, delay=delay)
    stats["events_discovered"] = len(events)

    if not events:
        logger.warning("No events found", extra={"source_id": source.id})
        stats["status"] = "success"
        logger.info("Big Waters collector completed", extra=stats)
        return stats

    now_utc = datetime.now(UTC)
    dry_run_items: list[dict[str, Any]] = []

    for idx, event in enumerate(events, start=1):
        try:
            event_url = event.get("link")
            if not event_url:
                stats["events_failed"] += 1
                logger.warning("Missing event URL", extra={"event_id": event.get("id")})
                continue

            raw_title = clean_text(event.get("title", {}).get("rendered")) or ""
            if SKIP_TITLE_RE.search(raw_title):
                stats["events_skipped_closed"] += 1
                logger.info(
                    "Skipping closure event",
                    extra={"event_id": event.get("id"), "title": raw_title},
                )
                continue

            detail = collect_event_detail(session, event_url)
            if not detail:
                stats["events_failed"] += 1
                continue

            if effective_future_only and detail["start_utc"] < now_utc:
                stats["events_skipped_past"] += 1
                continue

            collected = build_collected_event(event, detail)
            if not collected:
                stats["events_failed"] += 1
                continue

            ingest_event(db, source=source, event=collected, dry_run=dry_run)
            stats["events_collected"] += 1
            stats["occurrences_upserted"] += 1

            if dry_run:
                dry_run_items.append(_serialize_event(collected))

            if idx % 25 == 0:
                logger.info(
                    "Collection progress",
                    extra={
                        "processed": idx,
                        "total": len(events),
                        "collected": stats["events_collected"],
                        "failed": stats["events_failed"],
                    },
                )

            time.sleep(delay)
        except Exception as e:
            stats["errors"] += 1
            stats["events_failed"] += 1
            logger.error(
                "Failed to collect/ingest event",
                extra={
                    "event_id": event.get("id"),
                    "url": event.get("link"),
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
                exc_info=True,
            )

    if not dry_run:
        db.commit()
        logger.info("Database commit successful", extra={"source_id": source.id})
    else:
        write_test_data(
            "bigwaters",
            {
                "source_id": source.id,
                "source_name": source.name,
                "collected_at": datetime.now(UTC).isoformat(),
                "items": dry_run_items,
            },
        )

    stats["status"] = "success"
    logger.info("Big Waters collector completed", extra=stats)

    return stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    setup_logging()

    parser = argparse.ArgumentParser(
        description="Collect Big Waters Land Trust events via WordPress API"
    )
    add_common_args(parser)
    add_pagination_args(parser)
    add_feed_args(parser)
    parser.add_argument(
        "--include-past",
        action="store_true",
        help="Include past events (default: future events only)",
    )
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
            delay=args.delay,
            max_pages=args.max_pages,
            include_past=args.include_past,
            future_only=args.future_only,
            validate_ical=args.validate_ical,
            categories=args.categories,
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
