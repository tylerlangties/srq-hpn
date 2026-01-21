from __future__ import annotations

from datetime import UTC, datetime
from typing import Final

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.event_occurrence import EventOccurrence
from app.models.source import Source
from app.services.venue_resolver import resolve_venue_id

DEFAULT_TIMEZONE: Final[str] = "America/New_York"


def slugify(value: str) -> str:
    import re

    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def _truncate(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return value[:max_len].rstrip("-")


def _build_event_slug(*, title: str, source_id: int, external_id: str) -> str:
    base = slugify(title) or "event"

    frag = external_id.split("@", 1)[0]
    frag = slugify(frag) or "ext"
    frag = _truncate(frag, 24)

    slug = f"{base}-{source_id}-{frag}"
    return _truncate(slug, 120)


def _get_event(db: Session, *, source_id: int, external_id: str) -> Event | None:
    return db.scalar(
        select(Event).where(
            Event.source_id == source_id, Event.external_id == external_id
        )
    )


def _get_occurrence(
    db: Session, *, event_id: int, start_utc: datetime
) -> EventOccurrence | None:
    return db.scalar(
        select(EventOccurrence).where(
            EventOccurrence.event_id == event_id,
            EventOccurrence.start_datetime_utc == start_utc,
        )
    )


def upsert_event_and_occurrence(
    db: Session,
    *,
    source: Source,
    external_id: str,
    title: str,
    description: str | None,
    location: str | None,
    start_utc: datetime,
    end_utc: datetime | None,
    external_url: str | None,
    fallback_external_url: str | None,
) -> Event:
    """
    Generic iCal upsert:
      - Events dedupe: unique(source_id, external_id)
      - Occurrences dedupe: unique(event_id, start_datetime_utc)

    Stores raw LOCATION into EventOccurrence.location_text.
    Attempts deterministic venue match -> EventOccurrence.venue_id.
    """

    if start_utc.tzinfo is None:
        raise ValueError("start_utc must be timezone-aware (UTC)")

    if end_utc is not None and end_utc.tzinfo is None:
        raise ValueError("end_utc must be timezone-aware (UTC)")

    if end_utc is not None and end_utc < start_utc:
        end_utc = None

    final_url = external_url or fallback_external_url
    now = datetime.now(UTC)

    # ---- Event upsert (airtight with uniqueness constraint) ----
    event = _get_event(db, source_id=source.id, external_id=external_id)

    if event is None:
        slug = _build_event_slug(
            title=title, source_id=source.id, external_id=external_id
        )

        event = Event(
            title=title,
            description=description,
            slug=slug,
            is_free=False,  # unknown from iCal
            price_text=None,
            status="scheduled",
            source_id=source.id,
            external_id=external_id,
            external_url=final_url,
            last_seen_at=now,
            venue_id=None,  # important: venue is now on occurrences
        )
        db.add(event)

        try:
            db.flush()  # may raise if another process inserted same (source_id, external_id)
        except IntegrityError:
            db.rollback()
            event = _get_event(db, source_id=source.id, external_id=external_id)
            if event is None:
                raise
    else:
        event.title = title
        event.description = description
        event.external_url = final_url
        event.last_seen_at = now

    # ---- Occurrence upsert (airtight with uniqueness constraint) ----
    resolved_venue_id = resolve_venue_id(db, location)
    occ = _get_occurrence(db, event_id=event.id, start_utc=start_utc)

    if occ is None:
        occ = EventOccurrence(
            event_id=event.id,
            start_datetime_utc=start_utc,
            end_datetime_utc=end_utc,
            location_text=location,
            venue_id=resolved_venue_id,
        )
        db.add(occ)

        try:
            db.flush()  # may raise if another process inserted same (event_id, start_datetime_utc)
        except IntegrityError:
            db.rollback()
            occ = _get_occurrence(db, event_id=event.id, start_utc=start_utc)
            if occ is None:
                raise
            # If it already existed, update it (safe idempotency)
            occ.end_datetime_utc = end_utc
            occ.location_text = location
            occ.venue_id = resolved_venue_id
    else:
        occ.end_datetime_utc = end_utc
        occ.location_text = location
        occ.venue_id = resolved_venue_id

    return event
