"""
Big Top Brewing collector.

Discovers event iCal URLs via the Popmenu GraphQL API and stores them as
source_feeds for later ingestion.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
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
    is_future_event,
    upsert_source_feed,
    validate_ical_url,
    write_test_data,
)

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


def run_collector(
    db: Session,
    source: Source,
    *,
    delay: float = 0.25,
    validate_ical: bool = False,
    future_only: bool = False,
    categories: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Run the Big Top Brewing collector.

    Callable from both CLI and Celery tasks.
    """
    logger.info(
        "Starting Big Top Brewing collector",
        extra={
            "source_id": source.id,
            "categories": categories,
            "dry_run": dry_run,
            "validate_ical": validate_ical,
            "future_only": future_only,
            "delay": delay,
        },
    )

    stats: dict[str, Any] = {
        "source_id": source.id,
        "events_fetched": 0,
        "events_upserted": 0,
        "events_skipped_past": 0,
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

    dry_run_items: list[dict[str, Any]] = []

    for i, event in enumerate(events, start=1):
        try:
            slug = event.get("slug")
            if not slug:
                logger.warning(
                    "Event missing slug, skipping",
                    extra={"event_id": event.get("id"), "event": event},
                )
                continue

            ical_url = build_ical_url(slug)

            # Check if event is in the future
            if future_only:
                if not is_future_event(ical_url, session):
                    stats["events_skipped_past"] += 1
                    logger.debug(
                        "Skipping past event",
                        extra={
                            "source_id": source.id,
                            "slug": slug,
                            "name": event.get("name"),
                        },
                    )
                    time.sleep(delay)
                    continue
                time.sleep(delay)

            # Validate iCal URL
            if validate_ical:
                if validate_ical_url(ical_url, session):
                    stats["ical_validated"] += 1
                else:
                    stats["ical_invalid"] += 1
                    logger.warning(
                        "iCal URL validation failed, skipping",
                        extra={
                            "source_id": source.id,
                            "slug": slug,
                            "ical_url": ical_url,
                        },
                    )
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

            if dry_run:
                dry_run_items.append(
                    {
                        "external_id": external_id,
                        "name": event.get("name"),
                        "slug": slug,
                        "ical_url": ical_url,
                        "page_url": page_url,
                        "categories": categories,
                    }
                )

            if i % 25 == 0:
                logger.info(
                    "Upsert progress",
                    extra={
                        "source_id": source.id,
                        "processed": i,
                        "total": len(events),
                        "upserted": stats["events_upserted"],
                        "skipped_past": stats["events_skipped_past"],
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
