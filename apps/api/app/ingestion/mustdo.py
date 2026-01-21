# MUSTDO.COM INGESTION SCRIPT

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

import requests
from icalendar import Calendar  # type: ignore[import-untyped]

SRQ_TZ = ZoneInfo("America/New_York")

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
class IngestedOccurrence:
    external_id: str
    title: str
    description: str | None
    location: str | None
    start_utc: datetime
    end_utc: datetime | None
    external_url: str | None


def _coerce_dt_to_utc(value) -> datetime:
    """
    iCalendar can give us:
    - datetime with tzinfo
    - naive datetime (treat as SRQ local)
    - date-only (all-day)
    """
    if value is None:
        raise ValueError("Missing DTSTART")

    # date-only all-day event
    if hasattr(value, "year") and not hasattr(value, "hour"):
        # value is a date
        local = datetime.combine(value, time(0, 0), tzinfo=SRQ_TZ)
        return local.astimezone(UTC)

    # datetime
    dt: datetime = value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=SRQ_TZ)
    return dt.astimezone(UTC)


def fetch_ics(url: str) -> bytes:
    s = requests.Session()
    s.headers.update(HEADERS)

    resp = s.get(url, timeout=25, allow_redirects=True)
    resp.raise_for_status()
    return resp.content


def parse_mustdo_ics(ics_bytes: bytes, *, source_url: str) -> list[IngestedOccurrence]:
    cal = Calendar.from_ical(ics_bytes)
    out: list[IngestedOccurrence] = []

    for comp in cal.walk("VEVENT"):
        uid = str(comp.get("UID") or "").strip()
        if not uid:
            # must have external_id for de-dupe
            continue

        title = str(comp.get("SUMMARY") or "").strip()
        desc = str(comp.get("DESCRIPTION") or "").strip() or None
        location = str(comp.get("LOCATION") or "").strip() or None

        dtstart = comp.get("DTSTART")
        dtend = comp.get("DTEND")

        start_utc = _coerce_dt_to_utc(dtstart.dt if dtstart else None)
        end_utc = None
        if dtend is not None:
            end_utc = _coerce_dt_to_utc(dtend.dt)

        # MustDo gives us /events/<slug>/ical/ — store the non-ical page if possible
        external_url = source_url
        if external_url.endswith("/ical/"):
            external_url = external_url[: -len("ical/")]

        out.append(
            IngestedOccurrence(
                external_id=uid,
                title=title,
                description=desc,
                location=location,
                start_utc=start_utc,
                end_utc=end_utc,
                external_url=external_url,
            )
        )

    return out
