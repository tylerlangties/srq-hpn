from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.ical import fetch_ics, parse_ics
from app.models.source import Source
from app.models.source_feed import SourceFeed
from app.services.ingest_upsert import upsert_event_and_occurrence

logger = logging.getLogger(__name__)


def ingest_source_items(
    db: Session, *, source: Source, limit: int = 50
) -> dict[str, int]:
    """
    Fetch and ingest iCal URLs from source_feeds for this source.
    Feeds are idempotent due to DB uniqueness + upsert logic.

    Returns counts for debugging.
    """
    now = datetime.now(UTC)

    logger.debug(
        "Fetching source feeds",
        extra={"source_id": source.id, "source_name": source.name, "limit": limit},
    )

    items = db.scalars(
        select(SourceFeed)
        .where(SourceFeed.source_id == source.id)
        .order_by(SourceFeed.id.asc())
        .limit(limit)
    ).all()

    logger.info(
        "Found source feeds to process",
        extra={"source_id": source.id, "feeds_count": len(items)},
    )

    seen = 0
    ingested = 0
    errors = 0

    for item in items:
        seen += 1
        try:
            logger.debug(
                "Fetching iCal for source feed",
                extra={
                    "source_id": source.id,
                    "feed_id": item.id,
                    "ical_url": item.ical_url,
                },
            )
            ics_bytes = fetch_ics(item.ical_url)
            parsed = parse_ics(ics_bytes)  # usually 1 event, but can be many

            events_parsed_count = len(parsed)
            events_ingested_count = 0

            logger.debug(
                "Parsed iCal events",
                extra={
                    "source_id": source.id,
                    "feed_id": item.id,
                    "events_count": events_parsed_count,
                },
            )

            # Upsert each VEVENT
            # Note: ev.uid is the iCal event UID, which becomes Event.external_id
            # This is different from item.external_id (which identifies the iCal file/feed)
            for ev in parsed:
                upsert_event_and_occurrence(
                    db,
                    source=source,
                    external_id=ev.uid,  # iCal event UID -> Event.external_id (for deduplication)
                    title=ev.summary,
                    description=ev.description,
                    location=ev.location,
                    start_utc=ev.start_utc,
                    end_utc=ev.end_utc,
                    external_url=ev.url,
                    fallback_external_url=item.page_url,
                )
                events_ingested_count += 1
                ingested += 1

            # Mark fetched and update event counts
            item.last_fetched_at = now
            item.status = "ok"
            item.error = None
            item.events_parsed = events_parsed_count
            item.events_ingested = events_ingested_count

        except Exception as e:
            item.last_fetched_at = now
            item.status = "error"
            item.error = f"{type(e).__name__}: {e}"
            errors += 1
            logger.warning(
                "Error processing source feed",
                extra={
                    "source_id": source.id,
                    "feed_id": item.id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )

        # Keep things responsive if you're ingesting many items
        db.flush()

    logger.info(
        "Source feeds ingestion summary",
        extra={
            "source_id": source.id,
            "feeds_seen": seen,
            "events_ingested": ingested,
            "errors": errors,
        },
    )

    return {"feeds_seen": seen, "events_ingested": ingested, "errors": errors}
