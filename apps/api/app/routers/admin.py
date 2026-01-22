from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.ingestion.ical import fetch_ics, parse_ics
from app.models.source import Source
from app.services.ingest_source_items import ingest_source_items
from app.services.ingest_upsert import upsert_event_and_occurrence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/ingest", tags=["admin"])


@router.post("/source/{source_id}")
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


@router.post("/source/{source_id}/items")
def ingest_items_for_source(
    source_id: int, db: Session = Depends(get_db)
) -> dict[str, int]:
    logger.info("Starting source items ingestion", extra={"source_id": source_id})
    source = db.get(Source, source_id)
    if source is None:
        logger.warning(
            "Source not found for items ingestion", extra={"source_id": source_id}
        )
        return {"items_seen": 0, "events_ingested": 0, "errors": 1}

    result = ingest_source_items(db, source=source, limit=50)
    db.commit()
    logger.info(
        "Source items ingestion completed",
        extra={"source_id": source_id, **result},
    )
    return {"source_id": source_id, **result}
