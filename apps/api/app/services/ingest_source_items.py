from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.ical import fetch_ics, parse_ics
from app.models.source import Source
from app.models.source_item import SourceItem
from app.services.ingest_upsert import upsert_event_and_occurrence

logger = logging.getLogger(__name__)


def ingest_source_items(
    db: Session, *, source: Source, limit: int = 50
) -> dict[str, int]:
    """
    Fetch and ingest per-event iCal URLs from source_items for this source.
    Items are idempotent due to DB uniqueness + upsert logic.

    Returns counts for debugging.
    """
    now = datetime.now(UTC)

    logger.debug(
        "Fetching source items",
        extra={"source_id": source.id, "source_name": source.name, "limit": limit},
    )

    items = db.scalars(
        select(SourceItem)
        .where(SourceItem.source_id == source.id)
        .order_by(SourceItem.id.asc())
        .limit(limit)
    ).all()

    logger.info(
        "Found source items to process",
        extra={"source_id": source.id, "items_count": len(items)},
    )

    seen = 0
    ingested = 0
    errors = 0

    for item in items:
        seen += 1
        try:
            logger.debug(
                "Fetching iCal for source item",
                extra={
                    "source_id": source.id,
                    "item_id": item.id,
                    "ical_url": item.ical_url,
                },
            )
            ics_bytes = fetch_ics(item.ical_url)
            parsed = parse_ics(ics_bytes)  # usually 1 event, but can be many

            # Mark fetched regardless of parse count
            item.last_fetched_at = now
            item.status = "ok"
            item.error = None

            logger.debug(
                "Parsed iCal events",
                extra={
                    "source_id": source.id,
                    "item_id": item.id,
                    "events_count": len(parsed),
                },
            )

            # Upsert each VEVENT
            for ev in parsed:
                upsert_event_and_occurrence(
                    db,
                    source=source,
                    external_id=ev.uid,  # this is what makes it "airtight"
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
            logger.warning(
                "Error processing source item",
                extra={
                    "source_id": source.id,
                    "item_id": item.id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )

        # Keep things responsive if you're ingesting many items
        db.flush()

    logger.info(
        "Source items ingestion summary",
        extra={
            "source_id": source.id,
            "items_seen": seen,
            "events_ingested": ingested,
            "errors": errors,
        },
    )

    return {"items_seen": seen, "events_ingested": ingested, "errors": errors}
