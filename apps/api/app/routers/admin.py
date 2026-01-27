from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.ingestion.ical import fetch_ics, parse_ics
from app.models.source import Source
from app.models.source_feed import SourceFeed
from app.services.ingest_upsert import upsert_event_and_occurrence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


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
