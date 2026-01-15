from __future__ import annotations

from datetime import UTC, datetime
from typing import Final

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.event_occurrence import EventOccurrence
from app.models.source import Source
from app.models.venue import Venue

# Keep this consistent everywhere (matches your Venue default)
DEFAULT_TIMEZONE: Final[str] = "America/New_York"


def slugify(value: str) -> str:
    """
    Simple, stable slugify for internal use (matches your seed script style).
    """
    import re

    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def _truncate(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return value[:max_len].rstrip("-")


def get_or_create_venue_for_location(db: Session, location: str | None) -> Venue:
    """
    iCal LOCATION can be:
      - empty
      - a venue name
      - a full address string
      - multi-line strings

    For now we create a "best effort" Venue row keyed by a slug derived from
    LOCATION (or a stable TBD fallback). Later you can improve this with
    venue matching / normalization.
    """
    if not location or not location.strip():
        slug = "tbd"
        name = "TBD (Sarasota Area)"
        area = "Sarasota"
        address = "Sarasota, FL"
        website = None
    else:
        normalized = " ".join(location.split())  # collapse whitespace/newlines
        slug = slugify(normalized) or "tbd"
        slug = _truncate(slug, 120)

        # Keep within your column limits (Venue.name likely String(255))
        name = normalized[:255]
        area = "Sarasota"
        address = normalized[:255]
        website = None

    existing = db.scalar(select(Venue).where(Venue.slug == slug))
    if existing:
        return existing

    v = Venue(
        name=name,
        slug=slug,
        address=address,
        area=area,
        website=website,
        timezone=DEFAULT_TIMEZONE,
    )
    db.add(v)
    db.flush()
    return v


def _build_event_slug(*, title: str, source_id: int, external_id: str) -> str:
    """
    Produce a stable slug that is:
      - readable (includes title)
      - unlikely to collide across sources
      - deterministic (based on external_id)
    """
    base = slugify(title) or "event"

    # external_id can be long (or include @domain); keep only a short stable fragment
    frag = external_id.split("@", 1)[0]
    frag = slugify(frag) or "ext"
    frag = _truncate(frag, 24)

    slug = f"{base}-{source_id}-{frag}"
    return _truncate(slug, 120)


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
      - De-dupe Events by (source_id, external_id)
      - De-dupe occurrences by (event_id, start_datetime_utc)

    Notes:
      - iCal feeds often don't provide price/free info, so we leave those unknown.
      - Venue normalization is naive (LOCATION -> Venue). Improve later.

    Returns the Event.
    """
    if start_utc.tzinfo is None:
        raise ValueError("start_utc must be timezone-aware (UTC)")

    if end_utc is not None and end_utc.tzinfo is None:
        raise ValueError("end_utc must be timezone-aware (UTC)")

    if end_utc is not None and end_utc < start_utc:
        # Guard: some sources might do weird things; better to store None than invalid.
        end_utc = None

    venue = get_or_create_venue_for_location(db, location)

    final_url = external_url or fallback_external_url

    event = db.scalar(
        select(Event).where(
            Event.source_id == source.id, Event.external_id == external_id
        )
    )

    now = datetime.now(UTC)

    if event is None:
        slug = _build_event_slug(
            title=title, source_id=source.id, external_id=external_id
        )

        event = Event(
            title=title,
            description=description,
            venue_id=venue.id,
            slug=slug,
            is_free=False,  # Unknown from iCal; you can improve later
            price_text=None,
            status="scheduled",
            source_id=source.id,
            external_id=external_id,
            external_url=final_url,
            last_seen_at=now,
        )
        db.add(event)
        db.flush()
    else:
        # Minimal, safe updates
        event.title = title
        event.description = description
        event.venue_id = venue.id
        event.external_url = final_url
        event.last_seen_at = now

    # Occurrence upsert
    occ = db.scalar(
        select(EventOccurrence).where(
            EventOccurrence.event_id == event.id,
            EventOccurrence.start_datetime_utc == start_utc,
        )
    )

    if occ is None:
        db.add(
            EventOccurrence(
                event_id=event.id,
                start_datetime_utc=start_utc,
                end_datetime_utc=end_utc,
            )
        )
    else:
        # Update end time if it changed
        occ.end_datetime_utc = end_utc

    return event
