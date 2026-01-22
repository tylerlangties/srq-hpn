from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.event import Event
from app.models.event_occurrence import EventOccurrence
from app.models.venue import Venue
from app.models.venue_alias import VenueAlias
from app.schemas.admin import (
    AddAliasRequest,
    CreateVenueFromLocationRequest,
    LinkOccurrenceRequest,
    UnresolvedLocationGroup,
    UnresolvedOccurrenceOut,
    VenueOut,
)
from app.services.ingest_upsert import slugify
from app.services.venue_resolver import normalize_location

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/venues", tags=["admin"])


@router.get("/unresolved", response_model=list[UnresolvedLocationGroup])
def get_unresolved_locations(
    db: Session = Depends(get_db),
) -> list[UnresolvedLocationGroup]:
    """
    Get all unresolved locations grouped by location_text.
    Returns groups with occurrence counts and sample IDs.
    """
    # Find all occurrences with venue_id = NULL and non-null location_text
    stmt = (
        select(EventOccurrence.location_text, EventOccurrence.id)
        .where(EventOccurrence.venue_id.is_(None))
        .where(EventOccurrence.location_text.isnot(None))
        .order_by(
            EventOccurrence.location_text, EventOccurrence.start_datetime_utc.asc()
        )
    )

    results = db.execute(stmt).all()

    # Group by location_text in Python
    groups_dict: dict[str, list[int]] = {}
    for location_text, occ_id in results:
        if location_text not in groups_dict:
            groups_dict[location_text] = []
        groups_dict[location_text].append(occ_id)

    groups: list[UnresolvedLocationGroup] = []
    for location_text, occurrence_ids in sorted(
        groups_dict.items(), key=lambda x: len(x[1]), reverse=True
    ):
        # Limit sample IDs to first 5
        sample_ids = occurrence_ids[:5]
        groups.append(
            UnresolvedLocationGroup(
                location_text=location_text,
                normalized_location=normalize_location(location_text),
                occurrence_count=len(occurrence_ids),
                sample_occurrence_ids=sample_ids,
            )
        )

    logger.info(
        "Fetched unresolved locations",
        extra={"group_count": len(groups)},
    )
    return groups


@router.get(
    "/unresolved/{location_text}/occurrences",
    response_model=list[UnresolvedOccurrenceOut],
)
def get_occurrences_for_location(
    location_text: str,
    db: Session = Depends(get_db),
) -> list[UnresolvedOccurrenceOut]:
    """
    Get all occurrences for a specific unresolved location_text.
    """
    stmt = (
        select(EventOccurrence, Event.title)
        .join(Event, EventOccurrence.event_id == Event.id)
        .where(EventOccurrence.venue_id.is_(None))
        .where(EventOccurrence.location_text == location_text)
        .order_by(EventOccurrence.start_datetime_utc.asc())
    )

    results = db.execute(stmt).all()

    occurrences: list[UnresolvedOccurrenceOut] = []
    for occ, event_title in results:
        occurrences.append(
            UnresolvedOccurrenceOut(
                id=occ.id,
                start_datetime_utc=occ.start_datetime_utc,
                end_datetime_utc=occ.end_datetime_utc,
                location_text=occ.location_text,
                event_id=occ.event_id,
                event_title=event_title,
            )
        )

    return occurrences


@router.post("/link")
def link_occurrence_to_venue(
    request: LinkOccurrenceRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Link an occurrence to an existing venue.
    """
    occurrence = db.get(EventOccurrence, request.occurrence_id)
    if occurrence is None:
        raise HTTPException(status_code=404, detail="Occurrence not found")

    venue = db.get(Venue, request.venue_id)
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")

    occurrence.venue_id = request.venue_id
    db.commit()

    logger.info(
        "Linked occurrence to venue",
        extra={
            "occurrence_id": request.occurrence_id,
            "venue_id": request.venue_id,
        },
    )

    return {
        "ok": True,
        "occurrence_id": request.occurrence_id,
        "venue_id": request.venue_id,
    }


@router.post("/create-from-location")
def create_venue_from_location(
    request: CreateVenueFromLocationRequest,
    db: Session = Depends(get_db),
) -> VenueOut:
    """
    Create a new venue from location text and optionally link all matching occurrences.
    Automatically creates an alias from the location_text.
    """
    # Generate slug from name
    venue_slug = slugify(request.name)
    if not venue_slug:
        venue_slug = "venue"

    # Check for slug uniqueness
    existing = db.scalar(select(Venue).where(Venue.slug == venue_slug))
    if existing:
        # Append number if slug exists
        counter = 1
        while existing:
            new_slug = f"{venue_slug}-{counter}"
            existing = db.scalar(select(Venue).where(Venue.slug == new_slug))
            if not existing:
                venue_slug = new_slug
                break
            counter += 1

    # Create venue
    venue = Venue(
        name=request.name,
        slug=venue_slug,
        area=request.area,
        address=request.address,
    )
    db.add(venue)
    db.flush()  # Get the venue ID

    # Create alias from location_text
    normalized = normalize_location(request.location_text)
    alias = VenueAlias(
        venue_id=venue.id,
        alias=request.location_text,
        alias_normalized=normalized,
    )
    db.add(alias)

    # Optionally link all occurrences with matching location_text
    matching_occurrences = db.scalars(
        select(EventOccurrence).where(
            EventOccurrence.venue_id.is_(None),
            EventOccurrence.location_text == request.location_text,
        )
    ).all()

    linked_count = 0
    for occ in matching_occurrences:
        occ.venue_id = venue.id
        linked_count += 1

    db.commit()

    logger.info(
        "Created venue from location",
        extra={
            "venue_id": venue.id,
            "venue_name": venue.name,
            "linked_occurrences": linked_count,
        },
    )

    return VenueOut(
        id=venue.id,
        name=venue.name,
        slug=venue.slug,
        area=venue.area,
    )


@router.get("", response_model=list[VenueOut])
def list_venues(
    db: Session = Depends(get_db),
) -> list[VenueOut]:
    """
    List all venues (for selection in admin UI).
    """
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


@router.post("/{venue_id}/aliases")
def add_venue_alias(
    venue_id: int,
    request: AddAliasRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Add an alias to a venue.
    """
    venue = db.get(Venue, venue_id)
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")

    normalized = normalize_location(request.alias)

    # Check if alias already exists
    existing = db.scalar(
        select(VenueAlias).where(VenueAlias.alias_normalized == normalized)
    )
    if existing:
        if existing.venue_id == venue_id:
            return {"ok": True, "message": "Alias already exists for this venue"}
        raise HTTPException(
            status_code=400,
            detail=f"Alias already exists for venue {existing.venue_id}",
        )

    alias = VenueAlias(
        venue_id=venue_id,
        alias=request.alias,
        alias_normalized=normalized,
    )
    db.add(alias)
    db.commit()

    logger.info(
        "Added venue alias",
        extra={"venue_id": venue_id, "alias": request.alias},
    )

    return {"ok": True, "venue_id": venue_id, "alias": request.alias}
