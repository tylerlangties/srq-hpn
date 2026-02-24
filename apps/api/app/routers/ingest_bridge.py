from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.ingest_auth import require_ingest_token
from app.models.source import Source
from app.schemas.ingest_bridge import (
    BigtopIngestRejectedEvent,
    BigtopIngestRequest,
    BigtopIngestResponse,
)
from app.services.ingest_bigtop import is_bigtop_source
from app.services.ingest_upsert import upsert_event_and_occurrence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ingest", tags=["ingest-bridge"])

MAX_REJECTED_EVENT_ERRORS = 25


@router.post("/bigtop/events", response_model=BigtopIngestResponse)
def ingest_bigtop_events(
    body: BigtopIngestRequest,
    _: str = Depends(require_ingest_token),
    db: Session = Depends(get_db),
) -> BigtopIngestResponse:
    source = db.scalar(select(Source).where(Source.id == body.source_id))
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Source not found"
        )

    if not is_bigtop_source(source):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source is not Big Top",
        )

    upserted = 0
    rejected = 0
    rejected_events: list[BigtopIngestRejectedEvent] = []

    try:
        for event in body.events:
            try:
                upsert_event_and_occurrence(
                    db,
                    source=source,
                    external_id=event.external_id,
                    title=event.title,
                    description=event.description,
                    location=event.location,
                    start_utc=event.start_utc,
                    end_utc=event.end_utc,
                    external_url=event.external_url,
                    fallback_external_url=source.url,
                    categories=event.categories or None,
                )
                upserted += 1
            except Exception as exc:
                rejected += 1
                if len(rejected_events) < MAX_REJECTED_EVENT_ERRORS:
                    rejected_events.append(
                        BigtopIngestRejectedEvent(
                            external_id=event.external_id,
                            reason=f"{type(exc).__name__}: {exc}",
                        )
                    )

        db.commit()
    except Exception:
        db.rollback()
        raise

    logger.info(
        "Big Top ingest bridge completed",
        extra={
            "run_id": body.run_id,
            "source_id": body.source_id,
            "received": len(body.events),
            "upserted": upserted,
            "rejected": rejected,
            "rejected_details_count": len(rejected_events),
        },
    )

    return BigtopIngestResponse(
        run_id=body.run_id,
        source_id=body.source_id,
        received=len(body.events),
        upserted=upserted,
        rejected=rejected,
        rejected_events=rejected_events,
    )
