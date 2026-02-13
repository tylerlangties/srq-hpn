"""
Asolo Repertory Theatre collector.

Fetches shows from the WordPress REST API, scrapes each show page for
performance dates/times, and writes events + occurrences directly to the
database.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
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

BASE_URL = "https://asolorep.org"
SHOWS_API = f"{BASE_URL}/wp-json/wp/v2/show"

DEFAULT_VENUE = "Asolo Repertory Theatre, 5555 N Tamiami Trail, Sarasota, FL 34236"

EASTERN_TZ = ZoneInfo("America/New_York")

MONTH_MAP = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

TIME_RE = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", re.I)
DATE_RANGE_RE = re.compile(
    r"([A-Za-z]+)\s+(\d{1,2})\s*[-\u2013\u2014]\s*([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})",
    re.I,
)
DATE_RANGE_SAME_MONTH_RE = re.compile(
    r"([A-Za-z]+)\s+(\d{1,2})\s*[-\u2013\u2014]\s*(\d{1,2}),\s*(\d{4})",
    re.I,
)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class CollectedEvent:
    slug: str
    title: str
    description: str | None
    location: str
    dates: list[datetime]
    event_url: str


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def make_external_id(slug: str) -> str:
    return f"asolorep:{slug}"


def parse_month(value: str) -> int | None:
    if not value:
        return None
    return MONTH_MAP.get(value.strip().lower())


def parse_run_dates(text: str) -> tuple[datetime | None, datetime | None]:
    if not text:
        return (None, None)
    normalized = text.replace("\u2013", "-").replace("\u2014", "-")
    match = DATE_RANGE_RE.search(normalized)
    if match:
        start_month = parse_month(match.group(1))
        start_day = int(match.group(2))
        end_month = parse_month(match.group(3))
        end_day = int(match.group(4))
        year = int(match.group(5))

        if not start_month or not end_month:
            return (None, None)

        start_date = datetime(year, start_month, start_day, tzinfo=EASTERN_TZ)
        end_date = datetime(year, end_month, end_day, tzinfo=EASTERN_TZ)
        if end_date < start_date:
            end_date = end_date.replace(year=year + 1)
        return (start_date, end_date)

    match = DATE_RANGE_SAME_MONTH_RE.search(normalized)
    if not match:
        return (None, None)

    month = parse_month(match.group(1))
    start_day = int(match.group(2))
    end_day = int(match.group(3))
    year = int(match.group(4))
    if not month:
        return (None, None)

    start_date = datetime(year, month, start_day, tzinfo=EASTERN_TZ)
    end_date = datetime(year, month, end_day, tzinfo=EASTERN_TZ)
    return (start_date, end_date)


def extract_run_dates_text(soup: BeautifulSoup) -> str | None:
    info = soup.select_one(".event-intro__show-info")
    if info:
        for strong in info.find_all("strong"):
            label = (strong.get_text(strip=True) or "").lower()
            if label == "run dates":
                value = strong.find_next("p")
                if value:
                    return value.get_text(strip=True)

    hero = soup.select_one(".hero-event__headline")
    if hero:
        return hero.get_text(strip=True)
    return None


def parse_time_text(value: str) -> tuple[int, int] | None:
    match = TIME_RE.search(value or "")
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    marker = match.group(3).lower()

    if marker == "pm" and hour != 12:
        hour += 12
    if marker == "am" and hour == 12:
        hour = 0
    return (hour, minute)


def resolve_year_for_date(
    *,
    month: int,
    run_start: datetime | None,
    run_end: datetime | None,
    fallback_year: int | None,
) -> int | None:
    if run_start and run_end:
        if run_end.year > run_start.year and month < run_start.month:
            return run_end.year
        return run_start.year
    return fallback_year


def extract_show_times(
    soup: BeautifulSoup, *, run_start: datetime | None, run_end: datetime | None
) -> list[datetime]:
    show_times: list[datetime] = []

    for row in soup.select("section.show-times li.show-times__row"):
        date_node = row.select_one(".show-times__row-date")
        time_node = row.select_one(".show-times__row-time")
        date_text = date_node.get_text(strip=True) if date_node else ""
        time_text = time_node.get_text(strip=True) if time_node else ""

        match = re.search(r"([A-Za-z]+)\s+(\d{1,2})(?:,\s*(\d{4}))?", date_text)
        if not match:
            continue

        month = parse_month(match.group(1))
        day = int(match.group(2))
        year = int(match.group(3)) if match.group(3) else None
        if not month:
            continue

        year = resolve_year_for_date(
            month=month, run_start=run_start, run_end=run_end, fallback_year=year
        )
        if not year:
            continue

        parsed_time = parse_time_text(time_text)
        if not parsed_time:
            continue

        hour, minute = parsed_time
        local_dt = datetime(year, month, day, hour, minute, tzinfo=EASTERN_TZ)
        show_times.append(local_dt.astimezone(UTC))

    return sorted(set(show_times))


def extract_description(soup: BeautifulSoup) -> str | None:
    candidates = []
    for selector in [
        ".event-intro__copy",
        ".basic-copy__content",
        ".cards__stacked-card-copy",
    ]:
        for node in soup.select(selector):
            text = node.get_text(" ", strip=True)
            if text:
                candidates.append(text)

    if not candidates:
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            content = meta.get("content")
            if isinstance(content, str) and content.strip():
                candidates.append(content.strip())
    if not candidates:
        meta = soup.find("meta", attrs={"property": "og:description"})
        if meta:
            content = meta.get("content")
            if isinstance(content, str) and content.strip():
                candidates.append(content.strip())

    for text in candidates:
        cleaned = " ".join(text.split())
        if len(cleaned) >= 50:
            return cleaned[:2000]
    return None


def extract_location(soup: BeautifulSoup) -> str:
    info = soup.select_one(".event-intro__show-info")
    if info:
        for strong in info.find_all("strong"):
            label = (strong.get_text(strip=True) or "").lower()
            if label == "location":
                value = strong.find_next("p")
                if value:
                    location = value.get_text(" ", strip=True)
                    if location and "sarasota" not in location.lower():
                        return f"{location}, {DEFAULT_VENUE}"
                    if location:
                        return location
    return DEFAULT_VENUE


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------


def fetch_shows(session, *, max_pages: int = 10) -> list[dict[str, Any]]:
    shows: list[dict[str, Any]] = []
    page = 1

    while page <= max_pages:
        resp = session.get(
            SHOWS_API, params={"per_page": 100, "page": page}, timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break

        shows.extend(data)
        total_pages = int(resp.headers.get("X-WP-TotalPages", page))
        if page >= total_pages:
            break

        page += 1
        time.sleep(0.2)

    return shows


def fetch_html(session, url: str) -> str:
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def collect_show_page(
    session, *, url: str, slug: str, title: str
) -> CollectedEvent | None:
    html = fetch_html(session, url)
    soup = BeautifulSoup(html, "html.parser")

    run_dates_text = extract_run_dates_text(soup)
    run_start, run_end = parse_run_dates(run_dates_text or "")
    dates = extract_show_times(soup, run_start=run_start, run_end=run_end)
    if not dates:
        logger.warning("No show times found", extra={"url": url, "title": title})
        return None

    description = extract_description(soup)
    location = extract_location(soup)

    return CollectedEvent(
        slug=slug,
        title=title,
        description=description,
        location=location,
        dates=dates,
        event_url=url,
    )


def filter_future_dates(dates: list[datetime], *, now_utc: datetime) -> list[datetime]:
    return [dt for dt in dates if dt >= now_utc]


# ---------------------------------------------------------------------------
# Ingestion helper
# ---------------------------------------------------------------------------


def ingest_event(
    db: Session, *, source: Source, event: CollectedEvent, dry_run: bool = False
) -> int:
    external_id = make_external_id(event.slug)
    occurrences = 0

    for start_utc in event.dates:
        end_utc = start_utc + timedelta(hours=2)

        if dry_run:
            occurrences += 1
            continue

        upsert_event_and_occurrence(
            db,
            source=source,
            external_id=external_id,
            title=event.title,
            description=event.description,
            location=event.location,
            start_utc=start_utc,
            end_utc=end_utc,
            external_url=event.event_url,
            fallback_external_url=None,
        )
        occurrences += 1

    return occurrences


def _serialize_event(event: CollectedEvent) -> dict[str, Any]:
    return {
        "external_id": make_external_id(event.slug),
        "title": event.title,
        "description": event.description,
        "location": event.location,
        "event_url": event.event_url,
        "occurrences": [dt.isoformat() for dt in event.dates],
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
    future_only: bool = False,
    validate_ical: bool = False,
    categories: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Run the Asolo Rep collector.

    Callable from both CLI and Celery tasks.
    """
    logger.info(
        "Starting Asolo Rep collector",
        extra={
            "source_id": source.id,
            "dry_run": dry_run,
            "delay": delay,
            "max_pages": max_pages,
            "future_only": future_only,
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
        "pages_fetched": 0,
        "shows_found": 0,
        "shows_collected": 0,
        "shows_failed": 0,
        "occurrences_created": 0,
        "errors": 0,
    }

    now_utc = datetime.now(UTC)

    session = get_http_session(
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        },
    )

    shows = fetch_shows(session, max_pages=max_pages)
    stats["shows_found"] = len(shows)
    stats["pages_fetched"] = min(max_pages, (len(shows) + 99) // 100 if shows else 0)

    if not shows:
        logger.warning("No shows found", extra={"source_id": source.id})
        stats["status"] = "success"
        logger.info("Asolo Rep collector completed", extra=stats)
        return stats

    dry_run_items: list[dict[str, Any]] = []

    for i, show in enumerate(shows, start=1):
        try:
            slug = show.get("slug")
            title = (show.get("title") or {}).get("rendered") or slug or "Untitled"
            url = show.get("link")
            if not slug or not url:
                continue

            event = collect_show_page(session, url=url, slug=slug, title=title)
            if not event:
                stats["shows_failed"] += 1
                continue

            if future_only:
                filtered = filter_future_dates(event.dates, now_utc=now_utc)
                if not filtered:
                    stats["shows_failed"] += 1
                    continue
                event = CollectedEvent(
                    slug=event.slug,
                    title=event.title,
                    description=event.description,
                    location=event.location,
                    dates=filtered,
                    event_url=event.event_url,
                )

            stats["shows_collected"] += 1
            occurrences = ingest_event(db, source=source, event=event, dry_run=dry_run)
            stats["occurrences_created"] += occurrences

            if dry_run:
                dry_run_items.append(_serialize_event(event))

            if i % 10 == 0:
                logger.info(
                    "Collection progress",
                    extra={
                        "processed": i,
                        "total": len(shows),
                        "shows_collected": stats["shows_collected"],
                        "shows_failed": stats["shows_failed"],
                    },
                )

            time.sleep(delay)
        except Exception as e:
            stats["errors"] += 1
            stats["shows_failed"] += 1
            logger.error(
                "Failed to collect show",
                extra={
                    "show_id": show.get("id"),
                    "slug": show.get("slug"),
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
            "asolorep",
            {
                "source_id": source.id,
                "source_name": source.name,
                "collected_at": datetime.now(UTC).isoformat(),
                "future_only": future_only,
                "items": dry_run_items,
            },
        )

    stats["status"] = "success"
    logger.info("Asolo Rep collector completed", extra=stats)

    return stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    setup_logging()

    parser = argparse.ArgumentParser(
        description="Collect Asolo Rep show pages for performance dates"
    )
    add_common_args(parser)
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
            delay=args.delay,
            max_pages=args.max_pages,
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
                "error": str(e),
            },
            exc_info=True,
        )
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
