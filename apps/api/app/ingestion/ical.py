from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

import requests
from icalendar import Calendar  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

DEFAULT_TZ = ZoneInfo("America/New_York")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/calendar,text/plain;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


@dataclass(frozen=True)
class ParsedICalEvent:
    uid: str
    summary: str
    description: str | None
    location: str | None
    start_utc: datetime
    end_utc: datetime | None
    url: str | None
    categories: list[str]


def _normalize_categories(value: Any) -> list[str]:
    if value is None:
        return []

    raw_items: list[str]
    if hasattr(value, "cats"):
        raw_items = [str(item) for item in value.cats]
    elif isinstance(value, list | tuple | set):
        raw_items = [str(item) for item in value]
    else:
        raw_items = [str(item) for item in str(value).split(",")]

    seen: set[str] = set()
    categories: list[str] = []
    for item in raw_items:
        cleaned = item.strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        categories.append(cleaned)

    return categories


def fetch_ics(url: str) -> bytes:
    """Fetch iCal data from a URL."""
    logger.debug("Fetching iCal data", extra={"url": url})
    try:
        s = requests.Session()
        s.headers.update(HEADERS)
        resp = s.get(url, timeout=25, allow_redirects=True)
        resp.raise_for_status()
        logger.debug(
            "Successfully fetched iCal data",
            extra={"url": url, "content_length": len(resp.content)},
        )
        return resp.content
    except requests.RequestException as e:
        logger.error(
            "Failed to fetch iCal data",
            extra={"url": url, "error_type": type(e).__name__},
            exc_info=True,
        )
        raise


def _dt_to_utc(value: Any, *, default_tz: ZoneInfo) -> datetime:
    """
    Handles:
    - date (all-day) -> midnight local -> UTC
    - datetime naive -> assume default_tz -> UTC
    - datetime aware -> convert -> UTC
    """
    if value is None:
        raise ValueError("Missing DTSTART/DTEND")

    # date-only all-day
    if hasattr(value, "year") and not hasattr(value, "hour"):
        local = datetime.combine(value, time(0, 0), tzinfo=default_tz)
        return local.astimezone(UTC)

    dt: datetime = value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=default_tz)
    return dt.astimezone(UTC)


def parse_ics(
    ics_bytes: bytes,
    *,
    default_tz: ZoneInfo = DEFAULT_TZ,
) -> list[ParsedICalEvent]:
    """Parse iCal bytes into a list of events."""
    logger.debug("Parsing iCal data", extra={"bytes_length": len(ics_bytes)})
    try:
        cal = Calendar.from_ical(ics_bytes)
        out: list[ParsedICalEvent] = []

        for comp in cal.walk("VEVENT"):
            uid = str(comp.get("UID") or "").strip()
            if not uid:
                # If no UID, it's hard to reliably de-dupe.
                # You *can* synthesize later, but skip for now.
                logger.debug("Skipping event without UID")
                continue

            summary = str(comp.get("SUMMARY") or "").strip() or "(Untitled)"
            description = str(comp.get("DESCRIPTION") or "").strip() or None
            location = str(comp.get("LOCATION") or "").strip() or None
            categories = _normalize_categories(comp.get("CATEGORIES"))

            dtstart = comp.get("DTSTART")
            dtend = comp.get("DTEND")

            try:
                start_utc = _dt_to_utc(
                    dtstart.dt if dtstart else None, default_tz=default_tz
                )

                end_utc = None
                if dtend is not None:
                    end_utc = _dt_to_utc(dtend.dt, default_tz=default_tz)

                # Some feeds include a URL per event
                url = str(comp.get("URL") or "").strip() or None

                out.append(
                    ParsedICalEvent(
                        uid=uid,
                        summary=summary,
                        description=description,
                        location=location,
                        start_utc=start_utc,
                        end_utc=end_utc,
                        url=url,
                        categories=categories,
                    )
                )
            except (ValueError, AttributeError) as e:
                logger.warning(
                    "Error parsing event dates",
                    extra={"uid": uid, "error_type": type(e).__name__},
                    exc_info=True,
                )
                continue

        logger.info(
            "Successfully parsed iCal data",
            extra={"events_parsed": len(out), "default_tz": str(default_tz)},
        )
        return out
    except Exception as e:
        logger.error(
            "Failed to parse iCal data",
            extra={"error_type": type(e).__name__},
            exc_info=True,
        )
        raise
