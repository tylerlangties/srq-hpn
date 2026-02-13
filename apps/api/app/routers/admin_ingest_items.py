from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.models.source import Source
from app.models.user import UserRole
from app.services.ingest_source_items import ingest_source_items

router = APIRouter(
    prefix="/api/admin/ingest",
    tags=["admin-ingest"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


@router.post("/source/{source_id}/feeds")
def ingest_feeds_for_source(
    source_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    try:
        source = db.scalar(select(Source).where(Source.id == source_id))
        if source is None:
            raise ValueError(f"Source {source_id} not found")

        result = ingest_source_items(db, source=source, limit=limit)
        db.commit()
        return {
            "source_id": source_id,
            "feeds_seen": result["feeds_seen"],
            "events_ingested": result["events_ingested"],
            "errors": result["errors"],
            "cf_challenges": result["cf_challenges"],
        }
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
