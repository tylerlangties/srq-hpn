from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.event_occurrence import EventOccurrence
from app.models.source import Source
from app.models.source_feed import SourceFeed


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())


def make_signature(title: str | None, start_utc: datetime) -> tuple[str, datetime]:
    return (normalize_text(title), start_utc)


def is_bigtop_source(source: Source) -> bool:
    return bool(source.url and "bigtopbrewing.com" in source.url.lower())


def is_bigtop_rollup_feed(feed: SourceFeed) -> bool:
    external_id = (feed.external_id or "").lower()
    ical_url = (feed.ical_url or "").lower()
    page_url = (feed.page_url or "").lower()
    return (
        "happenings" in external_id
        or "happenings" in ical_url
        or "happenings" in page_url
    )


def prioritize_bigtop_feeds(items: Sequence[SourceFeed]) -> list[SourceFeed]:
    """Return feeds with rollup feeds moved to the end."""
    rollups = [item for item in items if is_bigtop_rollup_feed(item)]
    non_rollups = [item for item in items if item not in rollups]
    return non_rollups + rollups


def build_existing_signature_map(
    db: Session,
    *,
    source_id: int,
    start_times: set[datetime],
) -> dict[tuple[str, datetime], str]:
    """Map (normalized_title, start_utc) to existing external_id for Big Top."""
    if not start_times:
        return {}

    rows = db.execute(
        select(Event.title, EventOccurrence.start_datetime_utc, Event.external_id)
        .join(EventOccurrence, Event.id == EventOccurrence.event_id)
        .where(
            Event.source_id == source_id,
            Event.external_id.is_not(None),
            EventOccurrence.start_datetime_utc.in_(start_times),
        )
    ).all()

    out: dict[tuple[str, datetime], str] = {}
    for title, start_utc, external_id in rows:
        if not external_id:
            continue
        signature = make_signature(title, start_utc)
        out.setdefault(signature, external_id)
    return out
