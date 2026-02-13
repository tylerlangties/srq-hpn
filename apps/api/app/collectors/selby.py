"""
Selby Gardens collector.

Fetches events from the WordPress/MEC REST API and stores discovered iCal
URLs as source_feeds for later ingestion.

The MEC plugin does not expose event dates in the REST API response, only
WordPress post dates (published/modified).  To avoid downloading every
event's individual iCal just to check dates, we pre-filter at the API level
using the ``after`` parameter on the post published date.  This reduces the
result set from ~1 000 events to ~40, eliminating the need for per-event
HTTP calls via ``is_future_event``.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import requests
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

# Default lookback for the ``after`` API filter.  Events whose WordPress
# post was published more than this many months ago are excluded from the
# API response.  MEC event posts are typically created weeks to months
# before the event, so 6 months is a safe default that filters out the
# bulk of definitely-past events while keeping anything plausibly upcoming.
DEFAULT_PUBLISHED_MONTHS = 6

logger = logging.getLogger(__name__)

BASE_URL = "https://selby.org"
API_ENDPOINT = "/wp-json/wp/v2/mec-events"
CATEGORY_ENDPOINT = "/wp-json/wp/v2/mec_category"

# Category ID mappings (discovered from REST API)
CATEGORIES = {
    "adult-programs": 559,
    "classes": 561,
    "exhibits": 595,
    "special-events": 558,
    "youth-programs": 560,
}


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------


def build_ical_url(event_id: int) -> str:
    return f"{BASE_URL}/?method=ical&id={event_id}"


def make_external_id(event_id: int) -> str:
    return f"selby:{event_id}"


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------


def fetch_categories(session: requests.Session) -> dict[str, int]:
    """Fetch available MEC categories from API."""
    url = f"{BASE_URL}{CATEGORY_ENDPOINT}"
    logger.debug("Fetching categories", extra={"url": url})
    resp = session.get(url, timeout=30, params={"per_page": 100})
    resp.raise_for_status()
    categories = {cat["slug"]: cat["id"] for cat in resp.json()}
    logger.info(
        "Fetched categories",
        extra={"count": len(categories), "categories": list(categories.keys())},
    )
    return categories


def fetch_events_page(
    session: requests.Session,
    *,
    page: int = 1,
    per_page: int = 100,
    category_ids: list[int] | None = None,
    published_after: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Fetch a page of events from the REST API.

    Args:
        published_after: UTC ISO-8601 datetime string (``...Z``).  When
            provided, only
            events whose WordPress post was published after this date are
            returned (maps to the WP REST API ``after`` parameter).
    """
    url = f"{BASE_URL}{API_ENDPOINT}"
    params: dict[str, Any] = {"page": page, "per_page": per_page}
    if category_ids:
        params["mec_category"] = ",".join(str(cid) for cid in category_ids)
    if published_after:
        params["after"] = published_after

    logger.debug(
        "Fetching events page",
        extra={
            "url": url,
            "page": page,
            "category_ids": category_ids,
            "published_after": published_after,
        },
    )
    resp = session.get(url, timeout=30, params=params)
    resp.raise_for_status()

    total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
    events = resp.json()

    logger.debug(
        "Fetched events page",
        extra={"page": page, "events_count": len(events), "total_pages": total_pages},
    )
    return events, total_pages


def fetch_all_events(
    session: requests.Session,
    *,
    category_ids: list[int] | None = None,
    max_pages: int = 50,
    delay: float = 0.5,
    published_after: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch all events, paginating through results."""
    all_events: list[dict[str, Any]] = []
    page = 1

    while page <= max_pages:
        events, total_pages = fetch_events_page(
            session,
            page=page,
            per_page=100,
            category_ids=category_ids,
            published_after=published_after,
        )

        if not events:
            break

        all_events.extend(events)
        logger.info(
            "Fetched events",
            extra={
                "page": page,
                "total_pages": total_pages,
                "events_this_page": len(events),
                "total_collected": len(all_events),
                "published_after": published_after,
            },
        )

        if page >= total_pages:
            break

        page += 1
        time.sleep(delay)

    return all_events


# ---------------------------------------------------------------------------
# Core collector
# ---------------------------------------------------------------------------


def run_collector(
    db: Session,
    source: Source,
    *,
    delay: float = 0.5,
    max_pages: int = 50,
    filters: str | None = None,
    validate_ical: bool = False,
    future_only: bool = False,
    published_months: int | None = None,
    categories: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Run the Selby Gardens collector.

    Callable from both CLI and Celery tasks.

    When *future_only* is ``True`` (or *published_months* is set), the API
    query is filtered to events whose WordPress post was published within
    the last *published_months* months (default: ``DEFAULT_PUBLISHED_MONTHS``).
    This pre-filters ~1 000 events down to ~40 at the API level, avoiding
    the need to download each event's iCal individually.
    """
    # Resolve the published-after cutoff.  When --future-only is passed
    # without an explicit --published-months, we use the default lookback.
    published_after: str | None = None
    if future_only or published_months is not None:
        months = (
            published_months
            if published_months is not None
            else DEFAULT_PUBLISHED_MONTHS
        )
        cutoff = datetime.now(UTC) - timedelta(days=months * 30)
        # Keep this explicitly UTC so WP's ``after`` filter is unambiguous.
        published_after = (
            cutoff.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        )

    logger.info(
        "Starting Selby Gardens collector",
        extra={
            "source_id": source.id,
            "filters": filters,
            "categories": categories,
            "max_pages": max_pages,
            "delay": delay,
            "dry_run": dry_run,
            "validate_ical": validate_ical,
            "future_only": future_only,
            "published_after": published_after,
        },
    )

    stats: dict[str, Any] = {
        "source_id": source.id,
        "events_fetched": 0,
        "events_upserted": 0,
        "ical_validated": 0,
        "ical_invalid": 0,
        "errors": 0,
    }

    session = get_http_session(
        headers={"Accept": "application/json"},
    )

    # Resolve category filter slugs to IDs
    category_ids: list[int] | None = None
    if filters:
        slugs = [s.strip() for s in filters.split(",") if s.strip()]
        invalid = [s for s in slugs if s not in CATEGORIES]
        if invalid:
            raise SystemExit(
                f"Invalid filter slug(s): {invalid}. "
                f"Valid: {', '.join(sorted(CATEGORIES.keys()))}"
            )
        category_ids = [CATEGORIES[s] for s in slugs]
        logger.info(
            "Filtering by category slugs",
            extra={"filters": slugs, "category_ids": category_ids},
        )

    events = fetch_all_events(
        session,
        category_ids=category_ids,
        max_pages=max_pages,
        delay=delay,
        published_after=published_after,
    )
    stats["events_fetched"] = len(events)

    if not events:
        logger.warning("No events found", extra={"source_id": source.id})
        stats["status"] = "success"
        logger.info("Selby Gardens collector completed", extra=stats)
        return stats

    dry_run_items: list[dict[str, Any]] = []

    logger.info(
        "Processing events",
        extra={
            "source_id": source.id,
            "total_events": len(events),
            "validate_ical": validate_ical,
        },
    )

    for i, event in enumerate(events, start=1):
        try:
            event_id = event["id"]
            title = event.get("title", {}).get("rendered", "Unknown")
            ical_url = build_ical_url(event_id)

            # Validate iCal URL (requires HTTP request per event)
            if validate_ical:
                if validate_ical_url(ical_url, session):
                    stats["ical_validated"] += 1
                else:
                    stats["ical_invalid"] += 1
                    logger.warning(
                        "iCal URL validation failed, skipping",
                        extra={
                            "progress": f"{i}/{len(events)}",
                            "event_id": event_id,
                            "ical_url": ical_url,
                        },
                    )
                    time.sleep(delay)
                    continue
                time.sleep(delay)

            external_id = make_external_id(event_id)
            page_url = event.get("link", f"{BASE_URL}/events/")

            upsert_source_feed(
                db,
                source_id=source.id,
                external_id=external_id,
                page_url=page_url,
                ical_url=ical_url,
                categories=categories,
                dry_run=dry_run,
            )
            stats["events_upserted"] += 1

            logger.info(
                "Upserted event feed",
                extra={
                    "progress": f"{i}/{len(events)}",
                    "event_id": event_id,
                    "title": title,
                },
            )

            if dry_run:
                dry_run_items.append(
                    {
                        "external_id": external_id,
                        "event_id": event_id,
                        "title": title,
                        "ical_url": ical_url,
                        "page_url": page_url,
                        "categories": categories,
                    }
                )

            if i % 10 == 0:
                logger.info(
                    "Upsert progress",
                    extra={
                        "source_id": source.id,
                        "processed": i,
                        "total": len(events),
                        "upserted": stats["events_upserted"],
                    },
                )
        except Exception as e:
            stats["errors"] += 1
            logger.error(
                "Error upserting event",
                extra={
                    "source_id": source.id,
                    "event_id": event.get("id"),
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
            "selby",
            {
                "source_id": source.id,
                "source_name": source.name,
                "collected_at": datetime.now(UTC).isoformat(),
                "items": dry_run_items,
            },
        )

    stats["status"] = "success"
    logger.info("Selby Gardens collector completed", extra=stats)

    return stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    setup_logging()

    parser = argparse.ArgumentParser(
        description="Collect Selby Gardens events via REST API"
    )
    add_common_args(parser)
    add_pagination_args(parser, default_max_pages=50)
    add_feed_args(parser)
    parser.add_argument(
        "--filters",
        type=str,
        help=(
            "Comma-separated MEC category slugs to filter events "
            "(e.g. 'adult-programs,classes'). Events matching any slug are included."
        ),
    )
    parser.add_argument(
        "--published-months",
        type=int,
        default=None,
        help=(
            f"Only include events whose WP post was published within this many "
            f"months.  Activated automatically by --future-only (default: "
            f"{DEFAULT_PUBLISHED_MONTHS}).  Set explicitly to override."
        ),
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List available categories and exit",
    )
    args = parser.parse_args()

    # Handle --list-categories (no DB needed)
    if args.list_categories:
        session = get_http_session(headers={"Accept": "application/json"})
        categories = fetch_categories(session)
        print("\nAvailable categories:")
        for slug, cat_id in sorted(categories.items()):
            print(f"  {slug}: {cat_id}")
        return

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
            filters=args.filters,
            validate_ical=args.validate_ical,
            future_only=args.future_only,
            published_months=args.published_months,
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
