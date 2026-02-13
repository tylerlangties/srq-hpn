from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.ingestion.ical import fetch_ics, parse_ics
from app.models.event import Event
from app.models.event_occurrence import EventOccurrence
from app.models.source import Source
from app.models.source_feed import SourceFeed
from app.models.user import UserRole
from app.services.ingest_upsert import upsert_event_and_occurrence

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


class SourceFeedCleanupRequest(BaseModel):
    older_than_days: int = Field(
        ..., ge=1, le=365, description="Delete feeds not seen in this many days"
    )
    source_id: int | None = Field(
        None, description="Limit to this source; omit for all sources"
    )
    dry_run: bool = Field(
        False, description="If true, only return count, do not delete"
    )


class SourceOut(BaseModel):
    id: int
    name: str
    type: str
    feed_count: int


class EventSearchOut(BaseModel):
    id: int
    title: str
    source_name: str
    hidden: bool
    first_start_utc: str | None = None  # ISO datetime of earliest occurrence, if any


class EventHiddenUpdate(BaseModel):
    hidden: bool = Field(
        ..., description="Whether the event is hidden from the public API"
    )


class DuplicateGroupOut(BaseModel):
    title_norm: str
    start_utc: datetime
    occurrences: int
    event_ids: list[int]


class HideBulkRequest(BaseModel):
    event_ids: list[int] | None = Field(
        None, description="Event IDs to hide/unhide (takes precedence if set)"
    )
    source_name: str | None = Field(
        None, description="Source name (e.g. 'mustdo') when using external_ids"
    )
    external_ids: list[str] | None = Field(
        None, description="Event external_ids (requires source_name)"
    )
    hidden: bool = Field(True, description="Set hidden=True to hide, False to unhide")


@router.get("/events/search", response_model=list[EventSearchOut])
def search_events(
    q: str = Query(..., min_length=1, description="Title substring or event ID"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[EventSearchOut]:
    """
    Search events by title or by numeric event ID.
    Returns id, title, source_name, hidden, and earliest occurrence start (if any).
    """
    q = q.strip()
    if not q:
        return []

    cond = Event.title.ilike(f"%{q}%")
    if q.isdigit():
        cond = or_(Event.id == int(q), cond)

    first_occ = (
        select(
            EventOccurrence.event_id,
            func.min(EventOccurrence.start_datetime_utc).label("first_start"),
        )
        .group_by(EventOccurrence.event_id)
        .subquery()
    )
    stmt = (
        select(
            Event.id,
            Event.title,
            Event.hidden,
            Source.name.label("source_name"),
            first_occ.c.first_start,
        )
        .select_from(Event)
        .join(Source, Event.source_id == Source.id)
        .outerjoin(first_occ, Event.id == first_occ.c.event_id)
        .where(cond)
        .order_by(Event.id.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    return [
        EventSearchOut(
            id=r.id,
            title=r.title,
            source_name=r.source_name,
            hidden=r.hidden,
            first_start_utc=r.first_start.isoformat() if r.first_start else None,
        )
        for r in rows
    ]


@router.patch("/events/{event_id}")
def update_event_hidden(
    event_id: int,
    body: EventHiddenUpdate,
    db: Session = Depends(get_db),
) -> dict:
    """Set or clear the hidden flag on an event. Hidden events are excluded from public APIs."""
    event = db.scalar(select(Event).where(Event.id == event_id))
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    event.hidden = body.hidden
    db.commit()
    return {"event_id": event_id, "hidden": event.hidden}


@router.post("/events/hide-bulk")
def hide_events_bulk(
    body: HideBulkRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Bulk set hidden on events by event_ids or by (source_name, external_ids).
    Use event_ids for a known list of IDs; use source_name+external_ids for mustdo etc.
    """
    if body.event_ids:
        stmt = select(Event).where(Event.id.in_(body.event_ids))
        events = list(db.scalars(stmt).all())
        updated = sum(1 for e in events if e.hidden != body.hidden)
        for e in events:
            e.hidden = body.hidden
    elif body.source_name is not None and body.external_ids:
        source = db.scalar(select(Source).where(Source.name == body.source_name))
        if source is None:
            raise HTTPException(
                status_code=404, detail=f"Source '{body.source_name}' not found"
            )
        stmt = select(Event).where(
            Event.source_id == source.id,
            Event.external_id.in_(body.external_ids),
        )
        events = list(db.scalars(stmt).all())
        updated = sum(1 for e in events if e.hidden != body.hidden)
        for e in events:
            e.hidden = body.hidden
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either event_ids or (source_name and external_ids)",
        )
    db.commit()
    return {"updated": updated, "hidden": body.hidden}


@router.get("/sources", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)) -> Sequence[SourceOut]:
    """List all sources with their feed counts."""
    results = db.execute(
        select(
            Source.id,
            Source.name,
            Source.type,
            func.count(SourceFeed.id).label("feed_count"),
        )
        .outerjoin(SourceFeed, Source.id == SourceFeed.source_id)
        .group_by(Source.id, Source.name, Source.type)
        .order_by(Source.name)
    ).all()

    return [
        SourceOut(id=r.id, name=r.name, type=r.type, feed_count=r.feed_count)
        for r in results
    ]


@router.post("/source-feeds/cleanup")
def cleanup_source_feeds(
    body: SourceFeedCleanupRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Delete source_feeds that have not been seen by scrapers in at least
    older_than_days. Uses last_seen_at, or created_at when last_seen_at is null.
    """
    cutoff = datetime.now(UTC) - timedelta(days=body.older_than_days)
    base_cond = or_(
        SourceFeed.last_seen_at < cutoff,
        and_(
            SourceFeed.last_seen_at.is_(None),
            SourceFeed.created_at < cutoff,
        ),
    )
    if body.source_id is not None:
        base_cond = and_(base_cond, SourceFeed.source_id == body.source_id)

    if body.dry_run:
        count = db.scalar(select(func.count(SourceFeed.id)).where(base_cond)) or 0
        return {"would_delete": count}

    result = db.execute(delete(SourceFeed).where(base_cond))
    deleted = result.rowcount
    db.commit()
    logger.info(
        "Source feeds cleanup completed",
        extra={
            "deleted": deleted,
            "older_than_days": body.older_than_days,
            "source_id": body.source_id,
        },
    )
    return {"deleted": deleted}


@router.get("/events/duplicates", response_model=list[DuplicateGroupOut])
def list_event_duplicates(
    source_id: int = Query(..., ge=1, description="Source ID to scan"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[DuplicateGroupOut]:
    """
    List duplicate event occurrences by normalized title + start time.
    Useful for previewing dedupe candidates.
    """
    title_norm = func.regexp_replace(func.lower(Event.title), r"\s+", " ", "g").label(
        "title_norm"
    )
    start_utc = EventOccurrence.start_datetime_utc.label("start_utc")
    occurrences = func.count(EventOccurrence.id).label("occurrences")
    event_ids = func.array_agg(func.distinct(Event.id)).label("event_ids")

    stmt = (
        select(title_norm, start_utc, occurrences, event_ids)
        .join(EventOccurrence, EventOccurrence.event_id == Event.id)
        .where(Event.source_id == source_id)
        .group_by(title_norm, start_utc)
        .having(func.count(EventOccurrence.id) > 1)
        .order_by(occurrences.desc(), start_utc.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    return [
        DuplicateGroupOut(
            title_norm=r.title_norm,
            start_utc=r.start_utc,
            occurrences=r.occurrences,
            event_ids=list(r.event_ids or []),
        )
        for r in rows
    ]


@router.post("/ingest/source/{source_id}")
def ingest_source(source_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Ingest events directly from a source URL.

    Fetches and parses iCal data from the source URL, then upserts
    all events found in the feed.
    """
    logger.info("Starting source ingestion", extra={"source_id": source_id})

    try:
        source = db.scalar(select(Source).where(Source.id == source_id))
        if source is None:
            logger.warning("Source not found", extra={"source_id": source_id})
            raise HTTPException(status_code=404, detail="Source not found")

        if source.type != "ical":
            logger.warning(
                "Invalid source type",
                extra={"source_id": source_id, "source_type": source.type},
            )
            raise HTTPException(status_code=400, detail="Source type must be 'ical'")

        logger.debug(
            "Fetching iCal data", extra={"source_id": source_id, "url": source.url}
        )
        ics_bytes = fetch_ics(source.url)
        items = parse_ics(ics_bytes)
        logger.info(
            "Parsed iCal data",
            extra={"source_id": source_id, "events_found": len(items)},
        )

        ingested = 0
        for it in items:
            upsert_event_and_occurrence(
                db,
                source=source,
                external_id=it.uid,
                title=it.summary,
                description=it.description,
                location=it.location,
                start_utc=it.start_utc,
                end_utc=it.end_utc,
                external_url=it.url,
                fallback_external_url=source.url,
            )
            ingested += 1

        db.commit()
        logger.info(
            "Source ingestion completed",
            extra={
                "source_id": source.id,
                "events_seen": len(items),
                "events_ingested": ingested,
            },
        )
        return {
            "source_id": source.id,
            "events_seen": len(items),
            "events_ingested": ingested,
        }

    except HTTPException:
        # HTTPException is a FastAPI exception that should be re-raised
        # The session will be automatically closed by the dependency
        db.rollback()
        raise
    except Exception as e:
        # Rollback on any other exception to ensure data consistency
        db.rollback()
        logger.exception(
            "Error during source ingestion",
            extra={"source_id": source_id, "error_type": type(e).__name__},
        )
        # Return sanitized error message to client
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {type(e).__name__}"
        ) from e
    # Note: No finally block needed - FastAPI's dependency injection
    # automatically closes the session via get_db() generator
