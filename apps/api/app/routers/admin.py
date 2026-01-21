from __future__ import annotations

import traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db import SessionLocal
from app.ingestion.ical import fetch_ics, parse_ics
from app.models.source import Source
from app.services.ingest_source_items import ingest_source_items
from app.services.ingest_upsert import upsert_event_and_occurrence

router = APIRouter(prefix="/api/admin/ingest", tags=["admin"])


@router.post("/source/{source_id}")
def ingest_source(source_id: int) -> dict:
    db: Session = SessionLocal()
    try:
        source = db.scalar(select(Source).where(Source.id == source_id))
        if source is None:
            raise HTTPException(status_code=404, detail="Source not found")

        if source.type != "ical":
            raise HTTPException(status_code=400, detail="Source type must be 'ical'")

        ics_bytes = fetch_ics(source.url)
        items = parse_ics(ics_bytes)

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
        return {
            "source_id": source.id,
            "events_seen": len(items),
            "events_ingested": ingested,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        # Print full traceback to server logs
        traceback.print_exc()
        # Also return detail to client (dev-only behavior; fine for now)
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    finally:
        db.close()


@router.post("/source/{source_id}/items")
def ingest_items_for_source(
    source_id: int, db: Session = Depends(get_db)
) -> dict[str, int]:
    source = db.get(Source, source_id)
    if source is None:
        return {"items_seen": 0, "events_ingested": 0, "errors": 1}

    result = ingest_source_items(db, source=source, limit=50)
    db.commit()
    return {"source_id": source_id, **result}
