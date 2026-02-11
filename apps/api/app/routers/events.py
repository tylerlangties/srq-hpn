import logging
import re
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.models.event import Event
from app.models.event_occurrence import EventOccurrence
from app.schemas.events import (
    EventCountOut,
    EventDetailOut,
    EventOccurrenceOut,
    EventSlugResolutionOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events", tags=["events"])

SRQ_TZ = ZoneInfo("America/New_York")


def to_public_event_slug(raw_slug: str) -> str:
    trimmed = raw_slug.strip().lower()
    without_id_suffix = re.sub(r"-\d+-[a-z]{2,6}-[a-z0-9]{10,}$", "", trimmed)
    without_id_suffix = re.sub(r"-[a-z]{2,6}-[a-z0-9]{10,}$", "", without_id_suffix)
    without_id_suffix = re.sub(r"-[a-z0-9]{10,}$", "", without_id_suffix)
    return without_id_suffix or trimmed


def to_occurrence_payload(occ: EventOccurrence) -> dict[str, object]:
    return {
        "id": occ.id,
        "start_datetime_utc": occ.start_datetime_utc,
        "end_datetime_utc": occ.end_datetime_utc,
        "location_text": occ.location_text,
        "event": occ.event,
        "venue": occ.venue,
    }


@router.get("/day", response_model=list[EventOccurrenceOut])
def events_for_day(
    day: date = Query(..., description="Local date in YYYY-MM-DD (America/New_York)"),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Get events for a specific day."""
    logger.debug("Fetching events for day", extra={"day": str(day)})

    # Local day boundaries (SRQ timezone)
    local_start = datetime.combine(day, time.min, tzinfo=SRQ_TZ)
    local_end = datetime.combine(
        date.fromordinal(day.toordinal() + 1),
        time.min,
        tzinfo=SRQ_TZ,
    )

    start_utc = local_start.astimezone(UTC)
    end_utc = local_end.astimezone(UTC)

    stmt = (
        select(EventOccurrence)
        .join(Event, EventOccurrence.event_id == Event.id)
        .where(EventOccurrence.start_datetime_utc >= start_utc)
        .where(EventOccurrence.start_datetime_utc < end_utc)
        .where(Event.hidden.is_(False))
        .options(
            selectinload(EventOccurrence.event).selectinload(Event.categories),
            selectinload(EventOccurrence.venue),
        )
        .order_by(EventOccurrence.start_datetime_utc.asc())
    )

    occurrences = db.scalars(stmt).all()

    logger.info(
        "Found events for day",
        extra={"day": str(day), "count": len(occurrences)},
    )

    # Build response objects:
    # EventOccurrenceOut expects "venue" on the payload; we attach it from occurrence.venue.
    return [to_occurrence_payload(occ) for occ in occurrences]


@router.get("/range", response_model=list[EventOccurrenceOut])
def events_for_range(
    start: date = Query(
        ..., description="Start local date YYYY-MM-DD (America/New_York)"
    ),
    end: date = Query(
        ..., description="End local date YYYY-MM-DD (America/New_York), inclusive"
    ),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """
    Return all occurrences whose start_datetime_utc falls within the local date range
    [start 00:00, (end + 1 day) 00:00) converted to UTC.
    """
    logger.debug(
        "Fetching events for range", extra={"start": str(start), "end": str(end)}
    )

    if end < start:
        logger.warning(
            "Invalid date range",
            extra={"start": str(start), "end": str(end)},
        )
        # FastAPI will serialize this nicely for clients
        raise ValueError("end must be >= start")

    local_start = datetime.combine(start, time.min, tzinfo=SRQ_TZ)
    # inclusive end -> exclusive bound at next day midnight
    local_end_exclusive = datetime.combine(
        end + timedelta(days=1), time.min, tzinfo=SRQ_TZ
    )

    start_utc = local_start.astimezone(UTC)
    end_utc = local_end_exclusive.astimezone(UTC)

    stmt = (
        select(EventOccurrence)
        .join(Event, EventOccurrence.event_id == Event.id)
        .where(EventOccurrence.start_datetime_utc >= start_utc)
        .where(EventOccurrence.start_datetime_utc < end_utc)
        .where(Event.hidden.is_(False))
        .options(
            selectinload(EventOccurrence.event).selectinload(Event.categories),
            selectinload(EventOccurrence.venue),
        )
        .order_by(EventOccurrence.start_datetime_utc.asc())
    )

    occurrences = db.scalars(stmt).all()

    logger.info(
        "Found events for range",
        extra={"start": str(start), "end": str(end), "count": len(occurrences)},
    )

    return [to_occurrence_payload(occ) for occ in occurrences]


@router.get("/count", response_model=EventCountOut)
def events_count(
    start: date | None = Query(
        default=None,
        description="Optional start local date YYYY-MM-DD (America/New_York)",
    ),
    end: date | None = Query(
        default=None,
        description="Optional end local date YYYY-MM-DD (America/New_York), inclusive",
    ),
    db: Session = Depends(get_db),
) -> EventCountOut:
    """
    Return count of non-hidden event occurrences for a local date window.

    - If `start` and `end` are omitted, defaults to the current calendar week
      in America/New_York (Monday-Sunday).
    - If one is provided, both must be provided.
    """
    if (start is None) != (end is None):
        raise HTTPException(
            status_code=422,
            detail="start and end must both be provided, or both omitted",
        )

    if start is None and end is None:
        today_local = datetime.now(SRQ_TZ).date()
        start = today_local - timedelta(days=today_local.weekday())
        end = start + timedelta(days=6)

    assert start is not None
    assert end is not None

    if end < start:
        raise HTTPException(status_code=422, detail="end must be >= start")

    local_start = datetime.combine(start, time.min, tzinfo=SRQ_TZ)
    local_end_exclusive = datetime.combine(
        end + timedelta(days=1),
        time.min,
        tzinfo=SRQ_TZ,
    )

    start_utc = local_start.astimezone(UTC)
    end_utc = local_end_exclusive.astimezone(UTC)

    stmt = (
        select(func.count(EventOccurrence.id))
        .join(Event, EventOccurrence.event_id == Event.id)
        .where(EventOccurrence.start_datetime_utc >= start_utc)
        .where(EventOccurrence.start_datetime_utc < end_utc)
        .where(Event.hidden.is_(False))
    )

    count = db.scalar(stmt) or 0

    logger.info(
        "Counted events for range",
        extra={"start": str(start), "end": str(end), "count": count},
    )

    return EventCountOut(count=count, start=start, end=end)


@router.get("/resolve/{public_slug}", response_model=EventSlugResolutionOut)
def resolve_event_slug(
    public_slug: str,
    event_id: int | None = Query(
        default=None,
        description="Optional event id to resolve canonical path for.",
    ),
    db: Session = Depends(get_db),
) -> EventSlugResolutionOut:
    normalized_slug = public_slug.strip().lower()
    if not normalized_slug:
        raise HTTPException(status_code=404, detail="Event not found")

    event_stmt = (
        select(Event)
        .where(
            or_(
                Event.slug == normalized_slug,
                Event.slug.like(f"{normalized_slug}-%"),
            )
        )
        .where(Event.hidden.is_(False))
        .options(selectinload(Event.occurrences), selectinload(Event.categories))
    )
    candidates = list(db.scalars(event_stmt).all())

    if not candidates:
        raise HTTPException(status_code=404, detail="Event not found")

    now = datetime.now(UTC)
    ranked: list[tuple[Event, datetime]] = []
    for event in candidates:
        public_candidate_slug = to_public_event_slug(event.slug)
        if public_candidate_slug != normalized_slug:
            continue

        ordered_occurrences = sorted(
            event.occurrences,
            key=lambda occ: occ.start_datetime_utc,
        )
        if not ordered_occurrences:
            continue

        pivot_occurrence = next(
            (occ for occ in ordered_occurrences if occ.start_datetime_utc >= now),
            ordered_occurrences[0],
        )
        ranked.append((event, pivot_occurrence.start_datetime_utc))

    if not ranked:
        raise HTTPException(status_code=404, detail="Event not found")

    ranked.sort(key=lambda item: item[1])
    selected_event = ranked[0][0]

    if event_id is not None:
        match = next((event for event, _ in ranked if event.id == event_id), None)
        if not match:
            raise HTTPException(status_code=404, detail="Event not found")
        selected_event = match

    is_unique = len(ranked) == 1
    canonical_segment = (
        normalized_slug if is_unique else f"{normalized_slug}--e{selected_event.id}"
    )

    return EventSlugResolutionOut(
        event_id=selected_event.id,
        canonical_segment=canonical_segment,
        is_unique=is_unique,
    )


@router.get("/{event_id}", response_model=EventDetailOut)
def event_detail(event_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    """Get detail payload for a single event by id."""
    stmt = (
        select(EventOccurrence)
        .join(Event, EventOccurrence.event_id == Event.id)
        .where(EventOccurrence.event_id == event_id)
        .where(Event.hidden.is_(False))
        .options(
            selectinload(EventOccurrence.event).selectinload(Event.categories),
            selectinload(EventOccurrence.venue),
        )
        .order_by(EventOccurrence.start_datetime_utc.asc())
    )
    occurrences = list(db.scalars(stmt).all())

    if not occurrences:
        raise HTTPException(status_code=404, detail="Event not found")

    now = datetime.now(UTC)
    next_occurrence = next(
        (occ for occ in occurrences if occ.start_datetime_utc >= now),
        occurrences[0],
    )

    upcoming_occurrences = [
        occ for occ in occurrences if occ.start_datetime_utc >= now
    ][:8]
    if not upcoming_occurrences:
        upcoming_occurrences = [next_occurrence]

    more_from_venue: list[EventOccurrence] = []
    if next_occurrence.venue_id is not None:
        venue_stmt = (
            select(EventOccurrence)
            .join(Event, EventOccurrence.event_id == Event.id)
            .where(EventOccurrence.venue_id == next_occurrence.venue_id)
            .where(EventOccurrence.event_id != event_id)
            .where(EventOccurrence.start_datetime_utc >= now)
            .where(Event.hidden.is_(False))
            .options(
                selectinload(EventOccurrence.event).selectinload(Event.categories),
                selectinload(EventOccurrence.venue),
            )
            .order_by(EventOccurrence.start_datetime_utc.asc())
            .limit(4)
        )
        more_from_venue = list(db.scalars(venue_stmt).all())

    next_occurrence_out = to_occurrence_payload(next_occurrence)
    upcoming_occurrence_outs = [
        to_occurrence_payload(occ) for occ in upcoming_occurrences
    ]
    more_from_venue_outs = [to_occurrence_payload(occ) for occ in more_from_venue]

    return {
        "event": next_occurrence.event,
        "next_occurrence": next_occurrence_out,
        "upcoming_occurrences": upcoming_occurrence_outs,
        "more_from_venue": more_from_venue_outs,
    }
