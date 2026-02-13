"""
Sarasota Fair collector.

Fetches events from the Sarasota Fair's ``eventsservice.asmx`` API, parses
the nested day/time structure, and writes events + occurrences directly to
the database.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import requests
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

BASE_URL = "https://www.sarasotafair.com"
EVENTS_SERVICE_URL = f"{BASE_URL}/services/eventsservice.asmx"

EASTERN_TZ = ZoneInfo("America/New_York")

DEFAULT_START_HOUR = 12
DEFAULT_START_MINUTE = 0

TIME_RE = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*(AM|PM)", re.I)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class CollectedOccurrence:
    start_utc: datetime
    end_utc: datetime | None
    location: str | None


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def make_external_id(event_id: int) -> str:
    return f"sarasotafair:{event_id}"


def _post_json(
    session: requests.Session, url: str, payload: dict[str, Any]
) -> dict[str, Any]:
    resp = session.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_time_string(time_str: str) -> tuple[int, int] | None:
    if not time_str:
        return None

    text = time_str.strip().lower()
    if "noon" in text:
        return (12, 0)
    if "midnight" in text:
        return (0, 0)

    match = TIME_RE.search(time_str)
    if not match:
        return None

    return normalize_ampm_time(match.group(1), match.group(2), match.group(3))


def normalize_ampm_time(
    hour_str: str, minute_str: str | None, ampm: str
) -> tuple[int, int]:
    hour = int(hour_str)
    minute = int(minute_str or 0)
    marker = ampm.upper()

    if marker == "PM" and hour != 12:
        hour += 12
    if marker == "AM" and hour == 12:
        hour = 0

    return (hour, minute)


def parse_first_time(value: int | None) -> tuple[int, int] | None:
    if value is None:
        return None

    text = str(value)
    if len(text) <= 2:
        hour = 0
        minute = int(text)
    elif len(text) == 3:
        hour = int(text[0])
        minute = int(text[1:])
    else:
        hour = int(text[:2])
        minute = int(text[2:])

    if hour > 23 or minute > 59:
        return None

    return (hour, minute)


def parse_time_from_item(
    item: dict[str, Any],
) -> tuple[int, int, int | None, int | None]:
    time_range = (item.get("EventTimeRangeString") or "").strip()
    if time_range:
        lowered = time_range.lower()
        if "noon" in lowered or "midnight" in lowered:
            start = parse_time_string(time_range)
            matches = TIME_RE.findall(time_range)
            end = (
                normalize_ampm_time(matches[0][0], matches[0][1], matches[0][2])
                if matches
                else None
            )
            if start:
                return (
                    start[0],
                    start[1],
                    end[0] if end else None,
                    end[1] if end else None,
                )

        matches = TIME_RE.findall(time_range)
        if matches:
            start = normalize_ampm_time(matches[0][0], matches[0][1], matches[0][2])
            end = (
                normalize_ampm_time(matches[1][0], matches[1][1], matches[1][2])
                if len(matches) > 1
                else None
            )
            return (
                start[0],
                start[1],
                end[0] if end else None,
                end[1] if end else None,
            )

    if item.get("FirstTimeIsSpecified"):
        parsed = parse_first_time(item.get("FirstTime"))
        if parsed:
            return (parsed[0], parsed[1], None, None)

    if item.get("TimeIsSpecified"):
        parsed = parse_first_time(item.get("Time"))
        if parsed:
            return (parsed[0], parsed[1], None, None)

    return (DEFAULT_START_HOUR, DEFAULT_START_MINUTE, None, None)


def parse_date(date_text: str) -> datetime:
    return datetime.strptime(date_text, "%m/%d/%Y")


def clean_description(value: str | None) -> str | None:
    if not value:
        return None
    text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    if not text:
        return None
    return text[:2000]


def build_location(locations: list[dict[str, Any]] | None) -> str | None:
    if not locations:
        return None

    loc = locations[0]
    display = (loc.get("DisplayName") or loc.get("Name") or "").strip()
    address = (loc.get("AddressFormatted") or loc.get("Address") or "").strip()
    address = " ".join(address.replace("\r", " ").replace("\n", " ").split())

    if display and address:
        if display.lower() in address.lower():
            return address
        return f"{display}, {address}"
    if display:
        return display
    if address:
        return address
    return None


def build_occurrence(
    day: dict[str, Any], item: dict[str, Any]
) -> CollectedOccurrence | None:
    date_text = (item.get("DateSearchKey") or day.get("DateString") or "").strip()
    if not date_text:
        return None

    try:
        base_date = parse_date(date_text)
    except ValueError:
        logger.warning("Unable to parse date", extra={"date_text": date_text})
        return None

    hour, minute, end_hour, end_minute = parse_time_from_item(item)
    local_start = base_date.replace(hour=hour, minute=minute, tzinfo=EASTERN_TZ)
    start_utc = local_start.astimezone(UTC)

    end_utc = None
    if end_hour is not None and end_minute is not None:
        local_end = base_date.replace(
            hour=end_hour, minute=end_minute, tzinfo=EASTERN_TZ
        )
        end_utc = local_end.astimezone(UTC)
        if end_utc <= start_utc:
            end_utc = None

    return CollectedOccurrence(
        start_utc=start_utc,
        end_utc=end_utc,
        location=build_location(item.get("Locations") or []),
    )


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------


def fetch_event_days(session: requests.Session) -> list[str]:
    payload = {
        "day": "",
        "startDate": "",
        "endDate": "",
        "categoryID": 0,
        "currentUserItems": "false",
        "tagID": 0,
        "keywords": "",
        "isFeatured": "false",
        "fanPicks": "false",
        "myPicks": "false",
        "pastEvents": "false",
        "allEvents": "false",
        "memberEvents": "false",
        "memberOnly": "false",
        "showCategoryExceptionID": 0,
        "isolatedSchedule": 0,
        "customFieldFilters": [],
        "searchInDescription": False,
    }
    data = _post_json(session, f"{EVENTS_SERVICE_URL}/GetEventDays", payload)
    return data.get("d", [])


def fetch_event_days_by_list(
    session: requests.Session, dates: list[str]
) -> list[dict[str, Any]]:
    payload = {
        "dates": ",".join(dates),
        "day": "",
        "categoryID": 0,
        "tagID": 0,
        "keywords": "",
        "isFeatured": "false",
        "fanPicks": "false",
        "pastEvents": "false",
        "allEvents": "false",
        "memberEvents": "false",
        "memberOnly": "false",
        "showCategoryExceptionID": 0,
        "isolatedSchedule": 0,
        "customFieldFilters": [],
        "searchInDescription": False,
    }
    data = _post_json(session, f"{EVENTS_SERVICE_URL}/GetEventDaysByList", payload)
    return data.get("d", {}).get("Days", [])


def extract_events(days: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    seen_occurrences: set[tuple[int, datetime]] = set()

    for day in days:
        items: list[dict[str, Any]] = []
        for time_group in day.get("Times", []):
            items.extend(time_group.get("Items", []))
        items.extend(day.get("Unique", []))

        for item in items:
            event_id = item.get("EventID")
            name = (item.get("Name") or "").strip()
            if not event_id or not name:
                continue

            occurrence = build_occurrence(day, item)
            if not occurrence:
                continue

            occ_key = (event_id, occurrence.start_utc)
            if occ_key in seen_occurrences:
                continue
            seen_occurrences.add(occ_key)

            description = clean_description(item.get("LongDescription"))
            if not description:
                description = clean_description(item.get("ShortDescription"))

            event_url = item.get("ExternalLink") or item.get("DetailURL")
            events.append(
                {
                    "event_id": event_id,
                    "title": name,
                    "description": description,
                    "event_url": event_url,
                    "occurrence": occurrence,
                }
            )

    return events


# ---------------------------------------------------------------------------
# Ingestion helper
# ---------------------------------------------------------------------------


def ingest_event(
    db: Session, *, source: Source, event: dict[str, Any], dry_run: bool = False
) -> None:
    external_id = make_external_id(event["event_id"])
    occurrence: CollectedOccurrence = event["occurrence"]

    if dry_run:
        return

    upsert_event_and_occurrence(
        db,
        source=source,
        external_id=external_id,
        title=event["title"],
        description=event.get("description"),
        location=occurrence.location,
        start_utc=occurrence.start_utc,
        end_utc=occurrence.end_utc,
        external_url=event.get("event_url"),
        fallback_external_url=None,
    )


def _serialize_event(event: dict[str, Any]) -> dict[str, Any]:
    occurrence: CollectedOccurrence = event["occurrence"]
    return {
        "event_id": event.get("event_id"),
        "title": event.get("title"),
        "description": event.get("description"),
        "event_url": event.get("event_url"),
        "start_utc": occurrence.start_utc.isoformat(),
        "end_utc": occurrence.end_utc.isoformat() if occurrence.end_utc else None,
        "location": occurrence.location,
    }


# ---------------------------------------------------------------------------
# Core collector
# ---------------------------------------------------------------------------


def run_collector(
    db: Session,
    source: Source,
    *,
    delay: float = 0.5,
    max_days: int = 90,
    chunk_size: int = 10,
    max_pages: int = 10,
    validate_ical: bool = False,
    future_only: bool = False,
    categories: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Run the Sarasota Fair collector.

    Callable from both CLI and Celery tasks.
    """
    logger.info(
        "Starting Sarasota Fair collector",
        extra={
            "source_id": source.id,
            "dry_run": dry_run,
            "delay": delay,
            "max_days": max_days,
            "chunk_size": chunk_size,
            "max_pages": max_pages,
            "validate_ical": validate_ical,
            "future_only": future_only,
            "categories": categories,
        },
    )

    if max_pages != 10 or validate_ical or future_only or categories:
        logger.info(
            "Some standardized collector flags are accepted but not used by this collector",
            extra={
                "source_id": source.id,
                "max_pages": max_pages,
                "validate_ical": validate_ical,
                "future_only": future_only,
                "categories": categories,
            },
        )

    stats: dict[str, Any] = {
        "source_id": source.id,
        "days_fetched": 0,
        "events_discovered": 0,
        "occurrences_upserted": 0,
        "errors": 0,
    }

    session = get_http_session(
        headers={"Accept": "application/json, text/plain, */*"},
        allowed_methods=["POST", "GET"],
    )

    days = fetch_event_days(session)
    if max_days and max_days > 0:
        days = days[:max_days]
    stats["days_fetched"] = len(days)

    if not days:
        logger.warning("No event days found", extra={"source_id": source.id})
        stats["status"] = "success"
        return stats

    all_events: list[dict[str, Any]] = []
    for i in range(0, len(days), chunk_size):
        chunk = days[i : i + chunk_size]
        try:
            day_items = fetch_event_days_by_list(session, chunk)
            events = extract_events(day_items)
            all_events.extend(events)
            stats["events_discovered"] = len(all_events)

            logger.info(
                "Fetched event day chunk",
                extra={
                    "chunk_start": i + 1,
                    "chunk_size": len(chunk),
                    "events_in_chunk": len(events),
                    "total_events": stats["events_discovered"],
                },
            )
            time.sleep(delay)
        except Exception as e:
            stats["errors"] += 1
            logger.error(
                "Failed to fetch event day chunk",
                extra={
                    "chunk_start": i + 1,
                    "chunk_size": len(chunk),
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
                exc_info=True,
            )

    dry_run_items: list[dict[str, Any]] = []

    for idx, event in enumerate(all_events, start=1):
        try:
            ingest_event(db, source=source, event=event, dry_run=dry_run)
            stats["occurrences_upserted"] += 1

            if dry_run:
                dry_run_items.append(_serialize_event(event))

            if idx % 25 == 0:
                logger.info(
                    "Upsert progress",
                    extra={
                        "processed": idx,
                        "total": len(all_events),
                        "occurrences_upserted": stats["occurrences_upserted"],
                    },
                )
        except Exception as e:
            stats["errors"] += 1
            logger.error(
                "Failed to upsert event occurrence",
                extra={
                    "event_id": event.get("event_id"),
                    "title": event.get("title"),
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
            "sarasotafair",
            {
                "source_id": source.id,
                "source_name": source.name,
                "collected_at": datetime.now(UTC).isoformat(),
                "items": dry_run_items,
            },
        )

    stats["status"] = "success"
    logger.info("Sarasota Fair collector completed", extra=stats)

    return stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    setup_logging()

    parser = argparse.ArgumentParser(
        description="Collect Sarasota Fair events via eventsservice.asmx"
    )
    add_common_args(parser)
    add_pagination_args(parser)
    add_feed_args(parser)
    parser.add_argument(
        "--max-days",
        type=int,
        default=90,
        help="Limit number of event days to fetch (0 = no limit)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=10,
        help="Number of days to fetch per request (default: 10)",
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
            max_days=args.max_days,
            chunk_size=args.chunk_size,
            max_pages=args.max_pages,
            validate_ical=args.validate_ical,
            future_only=args.future_only,
            categories=args.categories,
            dry_run=args.dry_run,
        )

    except Exception:
        db.rollback()
        logger.critical(
            "Fatal error in collector",
            extra={"source_id": args.source_id},
            exc_info=True,
        )
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
