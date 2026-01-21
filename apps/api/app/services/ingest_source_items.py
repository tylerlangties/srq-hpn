from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.ical import fetch_ics, parse_ics
from app.models.source import Source
from app.models.source_item import SourceItem
from app.services.ingest_upsert import upsert_event_and_occurrence


def ingest_source_items(
    db: Session, *, source: Source, limit: int = 50
) -> dict[str, int]:
    """
    Fetch and ingest per-event iCal URLs from source_items for this source.
    Items are idempotent due to DB uniqueness + upsert logic.

    Returns counts for debugging.
    """
    now = datetime.now(UTC)

    items = db.scalars(
        select(SourceItem)
        .where(SourceItem.source_id == source.id)
        .order_by(SourceItem.id.asc())
        .limit(limit)
    ).all()

    seen = 0
    ingested = 0
    errors = 0

    for item in items:
        seen += 1
        try:
            ics_bytes = fetch_ics(item.ical_url)
            parsed = parse_ics(ics_bytes)  # usually 1 event, but can be many

            # Mark fetched regardless of parse count
            item.last_fetched_at = now
            item.status = "ok"
            item.error = None

            # Upsert each VEVENT
            for ev in parsed:
                upsert_event_and_occurrence(
                    db,
                    source=source,
                    external_id=ev.uid,  # this is what makes it “airtight”
                    title=ev.summary,
                    description=ev.description,
                    location=ev.location,
                    start_utc=ev.start_utc,
                    end_utc=ev.end_utc,
                    external_url=ev.url,
                    fallback_external_url=item.page_url,
                )
                ingested += 1

        except Exception as e:
            item.last_fetched_at = now
            item.status = "error"
            item.error = f"{type(e).__name__}: {e}"
            errors += 1

        # Keep things responsive if you’re ingesting many items
        db.flush()

    return {"items_seen": seen, "events_ingested": ingested, "errors": errors}
