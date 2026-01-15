from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

import requests
from icalendar import Calendar  # type: ignore[import-untyped]

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


def fetch_ics(url: str) -> bytes:
    s = requests.Session()
    s.headers.update(HEADERS)
    resp = s.get(url, timeout=25, allow_redirects=True)
    resp.raise_for_status()
    return resp.content


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
    cal = Calendar.from_ical(ics_bytes)
    out: list[ParsedICalEvent] = []

    for comp in cal.walk("VEVENT"):
        uid = str(comp.get("UID") or "").strip()
        if not uid:
            # If no UID, it's hard to reliably de-dupe.
            # You *can* synthesize later, but skip for now.
            continue

        summary = str(comp.get("SUMMARY") or "").strip() or "(Untitled)"
        description = str(comp.get("DESCRIPTION") or "").strip() or None
        location = str(comp.get("LOCATION") or "").strip() or None

        dtstart = comp.get("DTSTART")
        dtend = comp.get("DTEND")

        start_utc = _dt_to_utc(dtstart.dt if dtstart else None, default_tz=default_tz)

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
            )
        )

    return out
