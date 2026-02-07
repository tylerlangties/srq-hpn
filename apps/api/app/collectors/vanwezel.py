"""
Van Wezel Performing Arts Hall collector.

Scrapes the Van Wezel events listing, visits each event detail page, and
writes events + occurrences directly to the database.
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

BASE_URL = "https://www.vanwezel.org"
EVENTS_URL = f"{BASE_URL}/events/all"

# Van Wezel's address (constant for all events)
VENUE_LOCATION = "Van Wezel Performing Arts Hall, 777 N Tamiami Trl, Sarasota, FL 34236"

EASTERN_TZ = ZoneInfo("America/New_York")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class CollectedEvent:
    """Represents an event collected from Van Wezel."""

    slug: str
    title: str
    description: str | None
    dates: list[datetime]  # All occurrence dates (in UTC)
    event_url: str


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def make_external_id(slug: str) -> str:
    return f"vanwezel:{slug}"


def extract_slug_from_url(url: str) -> str:
    """Extract event slug from URL path."""
    if "/events/detail/" in url:
        path = url.split("/events/detail/")[-1]
    else:
        path = url.split("/events/")[-1]
    return path.rstrip("/").split("?")[0].split("#")[0]


def parse_date_text(date_text: str, year: int | None = None) -> list[datetime]:
    """
    Parse Van Wezel date formats into UTC datetimes.

    Handles:
    - "Thu. Jan 29, 2026" -> single date
    - "Jan 30 - 31, 2026" -> date range (same month)
    - "Jan 30, 2026 - Feb 1, 2026" -> date range (different months)

    Returns list of dates (one per day in range), each at 8pm local (typical showtime).
    """
    dates: list[datetime] = []
    date_text = date_text.strip()

    default_hour = 20

    # Clean up the text
    date_text = re.sub(r"^Date\s*", "", date_text, flags=re.I)
    weekdays = r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Thur)"
    date_text = re.sub(rf"^{weekdays}\.?\s*", "", date_text, flags=re.I)
    date_text = re.sub(r"([A-Za-z]{3})(\d)", r"\1 \2", date_text)
    date_text = re.sub(r"\s*-\s*", " - ", date_text)
    date_text = re.sub(r"\s+", " ", date_text)

    year_match = re.search(r"\b(20\d{2})\b", date_text)
    if year_match:
        year = int(year_match.group(1))
    elif year is None:
        year = datetime.now().year

    # Pattern: "Month DD - DD, YYYY" (same month range)
    same_month_range = re.match(
        r"([A-Za-z]+)\s+(\d{1,2})\s*-\s*(\d{1,2}),?\s*(\d{4})?", date_text
    )
    if same_month_range:
        month_str = same_month_range.group(1)
        start_day = int(same_month_range.group(2))
        end_day = int(same_month_range.group(3))
        if same_month_range.group(4):
            year = int(same_month_range.group(4))

        try:
            base_date = datetime.strptime(f"{month_str} 1, {year}", "%b %d, %Y")
            month = base_date.month
            for day in range(start_day, end_day + 1):
                local_dt = datetime(
                    year, month, day, default_hour, 0, tzinfo=EASTERN_TZ
                )
                dates.append(local_dt.astimezone(UTC))
            return dates
        except ValueError:
            pass

    # Pattern: "Month DD, YYYY - Month DD, YYYY" (different months)
    diff_month_range = re.match(
        r"([A-Za-z]+)\s+(\d{1,2}),?\s*(\d{4})?\s*-\s*([A-Za-z]+)\s+(\d{1,2}),?\s*(\d{4})?",
        date_text,
    )
    if diff_month_range:
        start_month = diff_month_range.group(1)
        start_day = int(diff_month_range.group(2))
        start_year = (
            int(diff_month_range.group(3)) if diff_month_range.group(3) else year
        )
        end_month = diff_month_range.group(4)
        end_day = int(diff_month_range.group(5))
        end_year = int(diff_month_range.group(6)) if diff_month_range.group(6) else year

        try:
            start_date = datetime.strptime(
                f"{start_month} {start_day}, {start_year}", "%b %d, %Y"
            )
            end_date = datetime.strptime(
                f"{end_month} {end_day}, {end_year}", "%b %d, %Y"
            )
            current = start_date
            while current <= end_date:
                local_dt = current.replace(
                    hour=default_hour, minute=0, tzinfo=EASTERN_TZ
                )
                dates.append(local_dt.astimezone(UTC))
                current += timedelta(days=1)
            return dates
        except ValueError:
            pass

    # Pattern: Single date "Month DD, YYYY"
    single_date = re.match(r"([A-Za-z]+)\s+(\d{1,2}),?\s*(\d{4})?", date_text)
    if single_date:
        month_str = single_date.group(1)
        day = int(single_date.group(2))
        if single_date.group(3):
            year = int(single_date.group(3))

        try:
            local_dt = datetime.strptime(
                f"{month_str} {day}, {year}", "%b %d, %Y"
            ).replace(hour=default_hour, minute=0, tzinfo=EASTERN_TZ)
            dates.append(local_dt.astimezone(UTC))
            return dates
        except ValueError:
            pass

    logger.warning("Could not parse date text", extra={"date_text": date_text})
    return dates


def extract_event_links(html: str) -> list[dict[str, Any]]:
    """Extract event links and basic info from the events listing page."""
    soup = BeautifulSoup(html, "html.parser")
    events: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for link in soup.find_all("a", href=re.compile(r"/events/detail/")):
        href = link.get("href", "")
        if not href:
            continue

        full_url = urljoin(BASE_URL, href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        card = link.find_parent(["div", "article", "li", "section"])

        title = ""
        date_text = ""

        if card:
            title_elem = card.find(["h2", "h3", "h4"])
            if title_elem:
                title = title_elem.get_text(strip=True)

            for text_node in card.stripped_strings:
                if re.search(r"[A-Za-z]{3}\.?\s+\d{1,2}", text_node):
                    date_text = text_node
                    break

        if not title:
            title = link.get_text(strip=True)
        if not title:
            slug = extract_slug_from_url(full_url)
            title = slug.replace("-", " ").title()

        events.append({"url": full_url, "title": title, "date_text": date_text})

    logger.info("Extracted event links", extra={"count": len(events)})
    return events


def parse_time_text(time_text: str) -> tuple[int, int]:
    """Parse time text like ``7:00 PM`` into (hour, minute) in 24h format."""
    time_match = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)", time_text, re.I)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        is_pm = time_match.group(3).upper() == "PM"
        if is_pm and hour != 12:
            hour += 12
        elif not is_pm and hour == 12:
            hour = 0
        return (hour, minute)
    return (20, 0)


def extract_showings_from_page(soup: BeautifulSoup) -> list[datetime]:
    """Extract all individual showings (date + time pairs) from an event detail page."""
    showings: list[datetime] = []

    for item in soup.find_all(class_="listItem"):
        date_elem = item.find(class_=re.compile(r"showings_date|singleDate"))
        time_elem = item.find(class_="time")

        if not date_elem:
            continue

        date_text = date_elem.get_text(strip=True)
        time_text = time_elem.get_text(strip=True) if time_elem else ""
        parsed_dates = parse_date_text(date_text)
        if not parsed_dates:
            continue

        hour, minute = parse_time_text(time_text) if time_text else (20, 0)

        for dt in parsed_dates:
            local_dt = dt.astimezone(EASTERN_TZ)
            adjusted = local_dt.replace(hour=hour, minute=minute)
            showings.append(adjusted.astimezone(UTC))

    if showings:
        return showings

    # Fallback to sidebar date range
    sidebar_date = soup.find(class_="sidebar_event_date")
    if sidebar_date:
        date_text = sidebar_date.get_text(strip=True)
        parsed = parse_date_text(date_text)
        if parsed:
            for dt in parsed:
                local_dt = dt.astimezone(EASTERN_TZ)
                adjusted = local_dt.replace(hour=20, minute=0)
                showings.append(adjusted.astimezone(UTC))

    return showings


def collect_event_detail(session, url: str) -> CollectedEvent | None:
    """Collect detailed event information from an event page."""
    try:
        html = fetch_html(session, url)
        soup = BeautifulSoup(html, "html.parser")

        slug = extract_slug_from_url(url)

        title_elem = soup.find("h1")
        title = (
            title_elem.get_text(strip=True)
            if title_elem
            else slug.replace("-", " ").title()
        )

        # Extract description
        description = None
        for cls in ["event_description", "description", "expandable"]:
            desc_elem = soup.find(class_=re.compile(rf"^{cls}$", re.I))
            if desc_elem:
                desc_text = desc_elem.get_text(strip=True)
                if len(desc_text) > 50 and not any(
                    skip in desc_text.lower()
                    for skip in ["group discount", "buy ticket", "menu"]
                ):
                    description = desc_text[:2000]
                    break

        if not description:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                content = meta_desc.get("content", "").strip()
                if content:
                    description = content

        if not description:
            og_desc = soup.find("meta", attrs={"property": "og:description"})
            if og_desc:
                content = og_desc.get("content", "").strip()
                if content:
                    description = content

        dates = extract_showings_from_page(soup)
        if not dates:
            logger.warning(
                "No dates found for event", extra={"url": url, "title": title}
            )
            return None

        dates = sorted(set(dates))

        return CollectedEvent(
            slug=slug, title=title, description=description, dates=dates, event_url=url
        )

    except Exception as e:
        logger.error(
            "Failed to collect event detail",
            extra={"url": url, "error_type": type(e).__name__, "error": str(e)},
            exc_info=True,
        )
        return None


def find_next_page_url(html: str, current_url: str) -> str | None:
    """Find the URL for the next page of events, if any."""
    soup = BeautifulSoup(html, "html.parser")

    next_link = soup.find("a", string=re.compile(r"more events|next|load more", re.I))
    if next_link and next_link.get("href"):
        return urljoin(current_url, next_link["href"])

    pagination = soup.find(class_=re.compile(r"pagination|pager", re.I))
    if pagination:
        next_btn = pagination.find("a", class_=re.compile(r"next", re.I))
        if next_btn and next_btn.get("href"):
            return urljoin(current_url, next_btn["href"])

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
    """Ingest a collected event into the database. Returns occurrence count."""
    external_id = make_external_id(event.slug)
    occurrences_count = 0

    for start_utc in event.dates:
        end_utc = start_utc + timedelta(hours=2, minutes=30)

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
                location=VENUE_LOCATION,
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
        "event_url": event.event_url,
        "location": VENUE_LOCATION,
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
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Run the Van Wezel collector.

    Callable from both CLI and Celery tasks.
    """
    logger.info(
        "Starting Van Wezel collector",
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

    # Phase 1: Fetch event listing pages
    all_event_links: list[dict[str, Any]] = []
    current_url: str | None = EVENTS_URL

    while current_url and stats["pages_fetched"] < max_pages:
        stats["pages_fetched"] += 1
        logger.info(
            "Fetching events listing page",
            extra={"page": stats["pages_fetched"], "url": current_url},
        )

        try:
            html = fetch_html(session, current_url)
            event_links = extract_event_links(html)
            all_event_links.extend(event_links)
            stats["events_discovered"] = len(all_event_links)

            current_url = find_next_page_url(html, current_url)
            if current_url:
                time.sleep(delay)

        except Exception as e:
            stats["errors"] += 1
            logger.error(
                "Failed to fetch events listing page",
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

    # Phase 2: Collect each event detail page
    dry_run_items: list[dict[str, Any]] = []

    for i, event_link in enumerate(unique_events, start=1):
        try:
            event = collect_event_detail(session, event_link["url"])
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

        if i % 10 == 0:
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
            "vanwezel",
            {
                "source_id": source.id,
                "source_name": source.name,
                "collected_at": datetime.now(UTC).isoformat(),
                "items": dry_run_items,
            },
        )

    stats["status"] = "success"
    logger.info("Van Wezel collector completed", extra=stats)

    return stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    setup_logging()

    parser = argparse.ArgumentParser(
        description="Collect Van Wezel Performing Arts Hall events"
    )
    add_common_args(parser)
    add_pagination_args(parser)
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
