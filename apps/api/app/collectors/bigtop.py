"""
Big Top Brewing collector.

Discovers event iCal URLs via the Popmenu GraphQL API and stores them as
source_feeds for later ingestion.

When ``--future-only`` is passed, the collector filters events by their
``createdAt`` timestamp from the GraphQL response (client-side, zero extra
HTTP requests) instead of downloading each event's iCal to check dates.
"""

from __future__ import annotations

import json
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
    get_http_session,
    upsert_source_feed,
    validate_ical_url,
    write_test_data,
)

# Default lookback for ``--future-only`` client-side filtering.  Events
# whose ``createdAt`` is older than this many months are skipped.
DEFAULT_CREATED_MONTHS = 6

logger = logging.getLogger(__name__)

BASE_URL = "https://www.bigtopbrewing.com"
EVENTS_PAGE = f"{BASE_URL}/restaurant-brewery-2"
GRAPHQL_URL = f"{BASE_URL}/graphql"
RESTAURANT_ID = 36499

GRAPHQL_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": BASE_URL,
    "Referer": EVENTS_PAGE,
}

EVENTS_QUERY = """
query CalendarEventsQuery($restaurantId: Int!) {
  calendarEvents(restaurantId: $restaurantId) {
    count
    records {
      id
      name
      slug
      createdAt
    }
  }
}
"""


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------


def build_ical_url(slug: str) -> str:
    return f"{BASE_URL}/events/{slug}.ics"


def build_page_url(slug: str) -> str:
    return f"{BASE_URL}/events/{slug}"


def make_external_id(slug: str) -> str:
    return f"bigtop:{slug}"


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------


def establish_session(session: requests.Session) -> None:
    """Visit the events page to establish session cookies for GraphQL."""
    logger.debug(
        "Establishing session by visiting events page", extra={"url": EVENTS_PAGE}
    )
    resp = session.get(EVENTS_PAGE, timeout=30)
    resp.raise_for_status()
    logger.debug(
        "Session established",
        extra={
            "status_code": resp.status_code,
            "cookies": list(session.cookies.keys()),
        },
    )


def fetch_events(session: requests.Session) -> list[dict[str, Any]]:
    """Fetch all events from the GraphQL endpoint."""
    logger.debug("Fetching events via GraphQL", extra={"url": GRAPHQL_URL})

    payload = json.dumps(
        {
            "query": EVENTS_QUERY,
            "variables": {"restaurantId": RESTAURANT_ID},
        }
    )

    resp = session.post(GRAPHQL_URL, data=payload, headers=GRAPHQL_HEADERS, timeout=30)
    resp.raise_for_status()

    data = resp.json()

    if "errors" in data:
        error_msg = data["errors"][0].get("message", "Unknown GraphQL error")
        logger.error(
            "GraphQL query failed",
            extra={"errors": data["errors"], "first_error": error_msg},
        )
        raise RuntimeError(f"GraphQL error: {error_msg}")

    events = data.get("data", {}).get("calendarEvents", {}).get("records", [])
    count = data.get("data", {}).get("calendarEvents", {}).get("count", 0)

    logger.info(
        "Fetched events from GraphQL",
        extra={"events_count": len(events), "total_count": count},
    )

    return events


# ---------------------------------------------------------------------------
# Core collector
# ---------------------------------------------------------------------------


def _parse_created_at(value: str | None) -> datetime | None:
    """Parse the ``createdAt`` field from the GraphQL response.

    Popmenu returns ISO-8601 strings like ``2026-02-01T03:37:36-05:00``.
    """
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except (ValueError, TypeError):
        return None


def run_collector(
    db: Session,
    source: Source,
    *,
    delay: float = 0.25,
    validate_ical: bool = False,
    future_only: bool = False,
    created_months: int | None = None,
    categories: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Run the Big Top Brewing collector.

    Callable from both CLI and Celery tasks.

    When *future_only* is ``True`` (or *created_months* is set), events are
    filtered client-side by their ``createdAt`` timestamp from the GraphQL
    response.  This avoids per-event iCal downloads entirely.
    """
    # Resolve the createdAt cutoff
    created_cutoff: datetime | None = None
    if future_only or created_months is not None:
        months = (
            created_months if created_months is not None else DEFAULT_CREATED_MONTHS
        )
        created_cutoff = datetime.now(UTC) - timedelta(days=months * 30)

    logger.info(
        "Starting Big Top Brewing collector",
        extra={
            "source_id": source.id,
            "categories": categories,
            "dry_run": dry_run,
            "validate_ical": validate_ical,
            "future_only": future_only,
            "created_cutoff": created_cutoff.isoformat() if created_cutoff else None,
            "delay": delay,
        },
    )

    stats: dict[str, Any] = {
        "source_id": source.id,
        "events_fetched": 0,
        "events_upserted": 0,
        "events_skipped_old": 0,
        "ical_validated": 0,
        "ical_invalid": 0,
        "errors": 0,
    }

    session = get_http_session(
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        },
        allowed_methods=["HEAD", "GET", "POST"],
    )

    # Establish session cookies for GraphQL
    establish_session(session)

    events = fetch_events(session)
    stats["events_fetched"] = len(events)

    if not events:
        logger.warning("No events found", extra={"source_id": source.id})
        stats["status"] = "success"
        return stats

    # Client-side filtering by createdAt (no HTTP requests)
    if created_cutoff:
        before_count = len(events)
        filtered: list[dict[str, Any]] = []
        for ev in events:
            created_at = _parse_created_at(ev.get("createdAt"))
            if created_at is None or created_at >= created_cutoff:
                filtered.append(ev)
            else:
                stats["events_skipped_old"] += 1
        events = filtered
        logger.info(
            "Filtered events by createdAt",
            extra={
                "source_id": source.id,
                "before": before_count,
                "after": len(events),
                "skipped_old": stats["events_skipped_old"],
                "cutoff": created_cutoff.isoformat(),
            },
        )

    logger.info(
        "Processing events",
        extra={
            "source_id": source.id,
            "total_events": len(events),
            "validate_ical": validate_ical,
        },
    )

    dry_run_items: list[dict[str, Any]] = []

    for i, event in enumerate(events, start=1):
        try:
            slug = event.get("slug")
            name = event.get("name", "Unknown")
            if not slug:
                logger.warning(
                    "Event missing slug, skipping",
                    extra={"event_id": event.get("id"), "event": event},
                )
                continue

            ical_url = build_ical_url(slug)

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
                            "slug": slug,
                            "ical_url": ical_url,
                        },
                    )
                    time.sleep(delay)
                    continue
                time.sleep(delay)

            external_id = make_external_id(slug)
            page_url = build_page_url(slug)

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
                    "slug": slug,
                    "event_name": name,
                },
            )

            if dry_run:
                dry_run_items.append(
                    {
                        "external_id": external_id,
                        "name": name,
                        "slug": slug,
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
                    "slug": event.get("slug"),
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
            "bigtop",
            {
                "source_id": source.id,
                "source_name": source.name,
                "collected_at": datetime.now(UTC).isoformat(),
                "items": dry_run_items,
            },
        )

    stats["status"] = "success"
    logger.info("Big Top Brewing collector completed", extra=stats)

    return stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    setup_logging()

    parser = argparse.ArgumentParser(
        description="Collect Big Top Brewing events via GraphQL and populate source_feeds"
    )
    add_common_args(parser, default_delay=0.25)
    add_feed_args(parser)
    parser.add_argument(
        "--created-months",
        type=int,
        default=None,
        help=(
            f"Only include events created within this many months.  "
            f"Activated automatically by --future-only (default: "
            f"{DEFAULT_CREATED_MONTHS}).  Set explicitly to override."
        ),
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
            validate_ical=args.validate_ical,
            future_only=args.future_only,
            created_months=args.created_months,
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
