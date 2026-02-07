"""
ArtFestival.com collector.

Scrapes the art festival calendar for Sarasota-area events, visits each
detail page, and writes events + occurrences directly to the database.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urljoin
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
    add_pagination_args,
    fetch_html,
    get_http_session,
    write_test_data,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://www.artfestival.com"
CALENDAR_URL = f"{BASE_URL}/calendar/festival"

EASTERN_TZ = ZoneInfo("America/New_York")

DEFAULT_START_HOUR = 10
DEFAULT_END_HOUR = 17

# Sarasota area locations to filter for
SARASOTA_AREA_PATTERNS = [
    r"\bsarasota\b",
    r"\blongboat\s*key\b",
    r"\bsiesta\s*key\b",
    r"\blakewood\s*ranch\b",
    r"\bvenice\b",
    r"\bbradenton\b",
    r"\bosprey\b",
    r"\bnokomis\b",
    r"\benglewood\b",
    r"\bnorth\s*port\b",
]

LOCATION_PATTERN = re.compile("|".join(SARASOTA_AREA_PATTERNS), re.IGNORECASE)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class CollectedEvent:
    slug: str
    title: str
    description: str | None
    dates: list[datetime]
    event_url: str
    location: str | None


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def make_external_id(slug: str) -> str:
    return f"artfestival:{slug}"


def extract_slug_from_url(url: str) -> str:
    path = url.split("/festivals/")[-1] if "/festivals/" in url else url
    parts = path.rstrip("/").split("/")
    return parts[0] if parts else path


def is_sarasota_area(text: str) -> bool:
    return bool(LOCATION_PATTERN.search(text))


def parse_date_range(date_text: str) -> list[datetime]:
    """
    Parse ArtFestival.com date formats into UTC datetimes.

    Handles: "February 7th & February 8th, 2026" etc.
    """
    dates: list[datetime] = []
    date_text = date_text.strip()

    if not date_text:
        return dates

    year_match = re.search(r"\b(20\d{2})\b", date_text)
    year = int(year_match.group(1)) if year_match else datetime.now().year

    date_pattern = re.compile(r"([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?", re.IGNORECASE)
    matches = date_pattern.findall(date_text)

    for month_str, day_str in matches:
        try:
            day = int(day_str)
            parsed = datetime.strptime(f"{month_str} {day}, {year}", "%B %d, %Y")
            local_dt = parsed.replace(
                hour=DEFAULT_START_HOUR, minute=0, tzinfo=EASTERN_TZ
            )
            dates.append(local_dt.astimezone(UTC))
        except ValueError as e:
            logger.warning(
                "Could not parse date component",
                extra={"month": month_str, "day": day_str, "error": str(e)},
            )

    return dates


def extract_event_links_from_calendar(html: str) -> list[dict[str, Any]]:
    """Extract Sarasota-area event links from the calendar page."""
    soup = BeautifulSoup(html, "html.parser")
    events: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for li in soup.find_all("li"):
        link = li.find("a", href=re.compile(r"/festivals/"))
        if not link:
            continue

        href = link.get("href", "")
        if not href:
            continue

        full_url = urljoin(BASE_URL, href)
        if full_url in seen_urls:
            continue

        full_text = li.get_text(strip=True)
        title = link.get_text(strip=True)

        location_match = re.search(r"\(([^)]+)\)", full_text)
        location = location_match.group(1) if location_match else ""

        if not (is_sarasota_area(title) or is_sarasota_area(location)):
            continue

        seen_urls.add(full_url)

        # Extract date text
        date_pattern = re.compile(
            r"([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?\s*&\s*(?:[A-Za-z]+\s+)?\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4})",
            re.IGNORECASE,
        )
        date_match = date_pattern.search(full_text)
        if date_match:
            date_text = date_match.group(1).strip()
        else:
            simple_date = re.search(
                r"^([A-Za-z]+\s+\d{1,2}[^A-Z]*\d{4})", full_text, re.IGNORECASE
            )
            if simple_date:
                date_text = simple_date.group(1).strip()
            else:
                date_text = full_text.replace(title, "").strip()
                if location_match:
                    date_text = date_text.replace(f"({location})", "").strip()

        events.append(
            {
                "url": full_url,
                "title": title,
                "date_text": date_text,
                "location": location,
            }
        )

    logger.info("Extracted Sarasota area event links", extra={"count": len(events)})
    return events


def find_next_page_url(html: str, current_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    next_link = soup.find("a", string=re.compile(r"next", re.I))
    if next_link and next_link.get("href"):
        return urljoin(current_url, next_link["href"])

    next_link = soup.find("a", rel="next")
    if next_link and next_link.get("href"):
        return urljoin(current_url, next_link["href"])

    return None


def collect_event_detail(
    session, url: str, calendar_data: dict[str, Any]
) -> CollectedEvent | None:
    """Collect detailed event information from a festival detail page."""
    try:
        html = fetch_html(session, url)
        soup = BeautifulSoup(html, "html.parser")

        slug = extract_slug_from_url(url)

        title_elem = soup.find("h1")
        title = (
            title_elem.get_text(strip=True)
            if title_elem
            else calendar_data.get("title", slug.replace("-", " ").title())
        )

        # Extract description
        description = None
        content_areas = soup.find_all(
            ["p", "div"], class_=re.compile(r"content|desc", re.I)
        )
        for area in content_areas:
            text = area.get_text(strip=True)
            if len(text) > 100:
                description = text[:2000]
                break

        if not description:
            main_content = soup.find("main") or soup.find(class_="content") or soup
            for elem in main_content.find_all(["p", "td"]):
                text = elem.get_text(strip=True)
                if len(text) > 150 and not any(
                    skip in text.lower()
                    for skip in [
                        "become an exhibitor",
                        "quick links",
                        "follow us",
                        "newsletter",
                    ]
                ):
                    description = text[:2000]
                    break

        if not description:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                content = meta_desc.get("content", "").strip()
                if content:
                    description = content

        # Extract location
        location = None
        maps_link = soup.find("a", href=re.compile(r"google.com/maps"))
        if maps_link:
            href = maps_link.get("href", "")
            if "search/" in href:
                addr_match = re.search(r"search/([^?]+)", href)
                if addr_match:
                    location = addr_match.group(1).replace("+", " ")
            elif "q=" in href:
                addr_match = re.search(r"q=([^&]+)", href)
                if addr_match:
                    from urllib.parse import unquote

                    location = unquote(addr_match.group(1).replace("+", " "))

        if not location:
            for text_elem in soup.find_all(
                string=re.compile(
                    r"\d+\s+\w+\s+(Street|St|Avenue|Ave|Blvd|Road|Rd)", re.I
                )
            ):
                parent = text_elem.find_parent()
                if parent:
                    text = parent.get_text(strip=True)
                    addr_match = re.search(
                        r"(\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Blvd|Road|Rd)[\w\s,]*FL\s*\d{5})",
                        text,
                        re.I,
                    )
                    if addr_match:
                        location = addr_match.group(1)
                        break

        if not location and calendar_data.get("location"):
            location = calendar_data["location"]

        # Parse dates
        dates: list[datetime] = []

        page_text = soup.get_text()
        detail_date_pattern = re.compile(
            r"(?:Saturday|Sunday|Monday|Tuesday|Wednesday|Thursday|Friday),?\s*"
            r"([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})"
            r"(?:\s+(\d{1,2}):(\d{2})\s*(am|pm))?",
            re.IGNORECASE,
        )
        detail_matches = detail_date_pattern.findall(page_text)

        if detail_matches:
            for match in detail_matches:
                month_str, day_str, year_str = match[0], match[1], match[2]
                hour_str, min_str, ampm = match[3], match[4], match[5]

                try:
                    day = int(day_str)
                    year = int(year_str)
                    parsed = datetime.strptime(
                        f"{month_str} {day}, {year}", "%B %d, %Y"
                    )

                    if hour_str and min_str and ampm:
                        hour = int(hour_str)
                        minute = int(min_str)
                        if ampm.lower() == "pm" and hour != 12:
                            hour += 12
                        elif ampm.lower() == "am" and hour == 12:
                            hour = 0
                    else:
                        hour = DEFAULT_START_HOUR
                        minute = 0

                    local_dt = parsed.replace(
                        hour=hour, minute=minute, tzinfo=EASTERN_TZ
                    )
                    dates.append(local_dt.astimezone(UTC))
                except ValueError:
                    pass

        if not dates:
            dates = parse_date_range(calendar_data.get("date_text", ""))

        dates = sorted(set(dates))

        if not dates:
            logger.warning(
                "No dates found for event",
                extra={
                    "url": url,
                    "title": title,
                    "calendar_date_text": calendar_data.get("date_text"),
                },
            )
            return None

        return CollectedEvent(
            slug=slug,
            title=title,
            description=description,
            dates=dates,
            event_url=url,
            location=location,
        )

    except Exception as e:
        logger.error(
            "Failed to collect event detail",
            extra={"url": url, "error_type": type(e).__name__, "error": str(e)},
            exc_info=True,
        )
        return None


# ---------------------------------------------------------------------------
# Ingestion helper
# ---------------------------------------------------------------------------


def ingest_event(
    db: Session,
    *,
    source: Source,
    event: CollectedEvent,
    dry_run: bool = False,
) -> int:
    """Ingest a collected event. Returns occurrence count."""
    external_id = make_external_id(event.slug)
    occurrences_count = 0

    for start_utc in event.dates:
        end_utc = start_utc + timedelta(hours=7)

        if dry_run:
            occurrences_count += 1
            continue

        try:
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
            occurrences_count += 1
        except Exception as e:
            logger.error(
                "Failed to upsert event occurrence",
                extra={
                    "external_id": external_id,
                    "title": event.title,
                    "start_utc": start_utc.isoformat(),
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
                exc_info=True,
            )

    return occurrences_count


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
    list_events: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Run the ArtFestival.com collector.

    Callable from both CLI and Celery tasks.
    """
    logger.info(
        "Starting ArtFestival.com collector",
        extra={
            "source_id": source.id,
            "dry_run": dry_run,
            "delay": delay,
            "max_pages": max_pages,
        },
    )

    stats: dict[str, Any] = {
        "source_id": source.id,
        "pages_fetched": 0,
        "events_discovered": 0,
        "events_collected": 0,
        "events_failed": 0,
        "occurrences_created": 0,
        "errors": 0,
    }

    session = get_http_session(
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        },
    )

    # Phase 1: Fetch calendar pages
    all_event_links: list[dict[str, Any]] = []
    current_url: str | None = CALENDAR_URL

    while current_url and stats["pages_fetched"] < max_pages:
        stats["pages_fetched"] += 1

        try:
            html = fetch_html(session, current_url)
            event_links = extract_event_links_from_calendar(html)
            all_event_links.extend(event_links)
            stats["events_discovered"] = len(all_event_links)

            current_url = find_next_page_url(html, current_url)
            if current_url:
                time.sleep(delay)

        except Exception as e:
            stats["errors"] += 1
            logger.error(
                "Failed to fetch calendar page",
                extra={
                    "page": stats["pages_fetched"],
                    "url": current_url,
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
                exc_info=True,
            )
            break

    # Deduplicate by URL
    seen_urls: set[str] = set()
    unique_events: list[dict[str, Any]] = []
    for event_link in all_event_links:
        if event_link["url"] not in seen_urls:
            seen_urls.add(event_link["url"])
            unique_events.append(event_link)

    logger.info(
        "Event discovery complete",
        extra={
            "total_discovered": len(all_event_links),
            "unique_events": len(unique_events),
            "pages_fetched": stats["pages_fetched"],
        },
    )

    # Handle --list-events
    if list_events:
        print("\nSarasota Area Events Found:")
        print("-" * 60)
        for event in unique_events:
            print(f"  {event['date_text']}")
            print(f"    {event['title']}")
            print(f"    Location: {event['location']}")
            print(f"    URL: {event['url']}")
            print()
        stats["status"] = "success"
        return stats

    # Phase 2: Collect each event detail page
    dry_run_items: list[dict[str, Any]] = []

    for i, event_link in enumerate(unique_events, start=1):
        try:
            event = collect_event_detail(session, event_link["url"], event_link)
            if event:
                stats["events_collected"] += 1
                occurrences = ingest_event(
                    db, source=source, event=event, dry_run=dry_run
                )
                stats["occurrences_created"] += occurrences

                if dry_run:
                    dry_run_items.append(_serialize_event(event))

                logger.info(
                    "Event collected",
                    extra={
                        "progress": f"{i}/{len(unique_events)}",
                        "title": event.title,
                        "dates_count": len(event.dates),
                        "occurrences": occurrences,
                        "location": event.location,
                    },
                )
            else:
                stats["events_failed"] += 1

            time.sleep(delay)

        except Exception as e:
            stats["errors"] += 1
            stats["events_failed"] += 1
            logger.error(
                "Failed to collect/ingest event",
                extra={
                    "url": event_link["url"],
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
                exc_info=True,
            )

        if i % 5 == 0:
            logger.info(
                "Collection progress",
                extra={
                    "processed": i,
                    "total": len(unique_events),
                    "collected": stats["events_collected"],
                    "failed": stats["events_failed"],
                },
            )

    if not dry_run:
        db.commit()
        logger.info("Database commit successful", extra={"source_id": source.id})
    else:
        write_test_data(
            "artfestival",
            {
                "source_id": source.id,
                "source_name": source.name,
                "collected_at": datetime.now(UTC).isoformat(),
                "items": dry_run_items,
            },
        )

    stats["status"] = "success"
    logger.info("ArtFestival.com collector completed", extra=stats)

    return stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    setup_logging()

    parser = argparse.ArgumentParser(
        description="Collect ArtFestival.com events for Sarasota area art/craft festivals"
    )
    add_common_args(parser)
    add_pagination_args(parser)
    parser.add_argument(
        "--list-events",
        action="store_true",
        help="Just list Sarasota area events found, don't collect details",
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
            list_events=args.list_events,
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
