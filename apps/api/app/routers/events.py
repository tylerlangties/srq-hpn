import logging
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.models.event import Event
from app.models.event_occurrence import EventOccurrence
from app.schemas.events import EventOccurrenceOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events", tags=["events"])

SRQ_TZ = ZoneInfo("America/New_York")


@router.get("/day", response_model=list[EventOccurrenceOut])
def events_for_day(
    day: date = Query(..., description="Local date in YYYY-MM-DD (America/New_York)"),
    db: Session = Depends(get_db),
) -> list[EventOccurrenceOut]:
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
            selectinload(EventOccurrence.event),
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
    results: list[EventOccurrenceOut] = []
    for occ in occurrences:
        results.append(
            EventOccurrenceOut(
                id=occ.id,
                start_datetime_utc=occ.start_datetime_utc,
                end_datetime_utc=occ.end_datetime_utc,
                location_text=occ.location_text,
                event=occ.event,  # type: ignore[arg-type]
                venue=occ.venue,  # type: ignore[arg-type]
            )
        )

    return results


@router.get("/range", response_model=list[EventOccurrenceOut])
def events_for_range(
    start: date = Query(
        ..., description="Start local date YYYY-MM-DD (America/New_York)"
    ),
    end: date = Query(
        ..., description="End local date YYYY-MM-DD (America/New_York), inclusive"
    ),
    db: Session = Depends(get_db),
) -> list[EventOccurrenceOut]:
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
            selectinload(EventOccurrence.event),
            selectinload(EventOccurrence.venue),
        )
        .order_by(EventOccurrence.start_datetime_utc.asc())
    )

    occurrences = db.scalars(stmt).all()

    logger.info(
        "Found events for range",
        extra={"start": str(start), "end": str(end), "count": len(occurrences)},
    )

    results: list[EventOccurrenceOut] = []
    for occ in occurrences:
        results.append(
            EventOccurrenceOut(
                id=occ.id,
                start_datetime_utc=occ.start_datetime_utc,
                end_datetime_utc=occ.end_datetime_utc,
                location_text=occ.location_text,
                event=occ.event,  # type: ignore[arg-type]
                venue=occ.venue,  # type: ignore[arg-type]
            )
        )

    return results
