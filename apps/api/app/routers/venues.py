import logging
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.models.event import Event
from app.models.event_occurrence import EventOccurrence
from app.models.venue import Venue
from app.schemas.events import EventOccurrenceOut, VenueDetailOut, VenueOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/venues", tags=["venues"])

SRQ_TZ = ZoneInfo("America/New_York")


@router.get("", response_model=list[VenueOut])
def list_venues(
    db: Session = Depends(get_db),
) -> list[VenueOut]:
    venues = db.scalars(select(Venue).order_by(Venue.name.asc())).all()
    return [
        VenueOut(
            id=v.id,
            name=v.name,
            slug=v.slug,
            area=v.area,
        )
        for v in venues
    ]


@router.get("/{slug}", response_model=VenueDetailOut)
def get_venue(
    slug: str,
    db: Session = Depends(get_db),
) -> VenueDetailOut:
    venue = db.scalar(select(Venue).where(Venue.slug == slug))
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")

    return VenueDetailOut(
        id=venue.id,
        name=venue.name,
        slug=venue.slug,
        area=venue.area,
        address=venue.address,
        website=venue.website,
        timezone=venue.timezone,
    )


@router.get("/{slug}/events", response_model=list[EventOccurrenceOut])
def events_for_venue(
    slug: str,
    start: date | None = Query(
        None, description="Start local date YYYY-MM-DD (America/New_York)"
    ),
    end: date | None = Query(
        None, description="End local date YYYY-MM-DD (America/New_York), inclusive"
    ),
    db: Session = Depends(get_db),
) -> list[EventOccurrenceOut]:
    venue = db.scalar(select(Venue).where(Venue.slug == slug))
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")

    if start is None:
        start = date.today()
    if end is None:
        end = start + timedelta(days=30)

    if end < start:
        raise HTTPException(status_code=400, detail="end must be >= start")

    local_start = datetime.combine(start, time.min, tzinfo=SRQ_TZ)
    local_end_exclusive = datetime.combine(
        end + timedelta(days=1), time.min, tzinfo=SRQ_TZ
    )

    start_utc = local_start.astimezone(UTC)
    end_utc = local_end_exclusive.astimezone(UTC)

    stmt = (
        select(EventOccurrence)
        .where(EventOccurrence.venue_id == venue.id)
        .where(EventOccurrence.start_datetime_utc >= start_utc)
        .where(EventOccurrence.start_datetime_utc < end_utc)
        .options(
            selectinload(EventOccurrence.event).selectinload(Event.categories),
            selectinload(EventOccurrence.venue),
        )
        .order_by(EventOccurrence.start_datetime_utc.asc())
    )

    occurrences = db.scalars(stmt).all()

    logger.info(
        "Found venue events",
        extra={
            "slug": slug,
            "venue_id": venue.id,
            "count": len(occurrences),
        },
    )

    return [
        EventOccurrenceOut(
            id=occ.id,
            start_datetime_utc=occ.start_datetime_utc,
            end_datetime_utc=occ.end_datetime_utc,
            location_text=occ.location_text,
            event=occ.event,  # type: ignore[arg-type]
            venue=occ.venue,  # type: ignore[arg-type]
        )
        for occ in occurrences
    ]
