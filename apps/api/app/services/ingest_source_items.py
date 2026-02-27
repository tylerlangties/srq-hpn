from __future__ import annotations

import logging
import random
import time
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.ical import (
    CloudflareChallengeError,
    create_ical_session,
    fetch_ics,
    parse_ics,
    warm_session,
)
from app.models.source import Source
from app.models.source_feed import SourceFeed
from app.services.categorize import filter_known_categories
from app.services.ingest_bigtop import (
    build_existing_signature_map,
    is_bigtop_source,
    make_signature,
    prioritize_bigtop_feeds,
)
from app.services.ingest_sink import IngestEventPayload, IngestEventSink
from app.services.ingest_upsert import upsert_event_and_occurrence

logger = logging.getLogger(__name__)

# Default delay between iCal fetches (seconds).  Keeps request rate low
# enough to avoid triggering Cloudflare rate-limit challenges.
DEFAULT_FETCH_DELAY: float = 0.5


def ingest_source_items(
    db: Session,
    *,
    source: Source,
    limit: int = 50,
    delay: float = DEFAULT_FETCH_DELAY,
    sink: IngestEventSink | None = None,
) -> dict[str, int]:
    """
    Fetch and ingest iCal URLs from source_feeds for this source.
    Feeds are idempotent due to DB uniqueness + upsert logic.

    A shared :class:`requests.Session` is used for all feeds in the batch
    so that Cloudflare cookies persist across requests.  A brief delay
    (configurable via *delay*) is inserted between fetches to stay under
    rate-limit thresholds.

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

    is_bigtop = is_bigtop_source(source)
    if is_bigtop and items:
        # Required due to weird bigtop event structure, prevents duplicates
        # Big top has a monthly "roundup" event ical that needs to be last (for deduping properly)
        items = prioritize_bigtop_feeds(items)

    logger.info(
        "Found source feeds to process",
        extra={"source_id": source.id, "feeds_count": len(items)},
    )

    # --- Shared session with Cloudflare cookie persistence ----------------
    session = create_ical_session()
    if items:
        first_url = items[0].ical_url
        if first_url:
            warm_session(session, first_url)

    seen = 0
    ingested = 0
    errors = 0
    cf_challenges = 0
    seen_signatures: set[tuple[str, datetime]] = set()

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
            ics_bytes = fetch_ics(item.ical_url, session=session)
            parsed = parse_ics(ics_bytes)  # usually 1 event, but can be many

            existing_signature_map: dict[tuple[str, datetime], str] = {}
            if is_bigtop:
                start_times = {ev.start_utc for ev in parsed}
                existing_signature_map = build_existing_signature_map(
                    db,
                    source_id=source.id,
                    start_times=start_times,
                )

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
                # Collect explicit categories from iCal + source_feed.
                # Both sources are filtered against the known registry
                # to discard garbage values that many iCal feeds emit
                # and to prevent stale SourceFeed.categories from
                # creating unknown category rows.
                explicit_cats: list[str] = filter_known_categories(ev.categories)
                if item.categories:
                    explicit_cats.extend(
                        filter_known_categories(
                            cat.strip()
                            for cat in item.categories.split(",")
                            if cat.strip()
                        )
                    )

                signature = make_signature(ev.summary, ev.start_utc)

                if is_bigtop:
                    if signature in seen_signatures:
                        logger.info(
                            "Skipping duplicate Big Top event in run",
                            extra={
                                "source_id": source.id,
                                "feed_id": item.id,
                                "title": ev.summary,
                                "start_utc": ev.start_utc.isoformat(),
                            },
                        )
                        continue

                    existing_external_id = existing_signature_map.get(signature)
                    if existing_external_id:
                        upsert_event_and_occurrence(
                            db,
                            source=source,
                            external_id=existing_external_id,
                            title=ev.summary,
                            description=ev.description,
                            location=ev.location,
                            start_utc=ev.start_utc,
                            end_utc=ev.end_utc,
                            external_url=ev.url,
                            fallback_external_url=item.page_url,
                            categories=explicit_cats or None,
                        )
                        if sink is not None:
                            sink.on_event(
                                source=source,
                                event=IngestEventPayload(
                                    external_id=existing_external_id,
                                    title=ev.summary,
                                    description=ev.description,
                                    location=ev.location,
                                    start_utc=ev.start_utc,
                                    end_utc=ev.end_utc,
                                    external_url=ev.url or item.page_url,
                                    categories=explicit_cats,
                                ),
                            )
                        events_ingested_count += 1
                        ingested += 1
                        seen_signatures.add(signature)
                        continue

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
                    categories=explicit_cats or None,
                )
                if sink is not None:
                    sink.on_event(
                        source=source,
                        event=IngestEventPayload(
                            external_id=ev.uid,
                            title=ev.summary,
                            description=ev.description,
                            location=ev.location,
                            start_utc=ev.start_utc,
                            end_utc=ev.end_utc,
                            external_url=ev.url or item.page_url,
                            categories=explicit_cats,
                        ),
                    )

                events_ingested_count += 1
                ingested += 1
                if is_bigtop:
                    seen_signatures.add(signature)

            # Mark fetched and update event counts
            item.last_fetched_at = now
            item.status = "ok"
            item.error = None
            item.events_parsed = events_parsed_count
            item.events_ingested = events_ingested_count

        except CloudflareChallengeError:
            cf_challenges += 1
            item.last_fetched_at = now
            item.status = "cf_blocked"
            item.error = "Cloudflare challenge - will retry on next run"
            logger.warning(
                "Cloudflare challenge persisted after retries",
                extra={
                    "source_id": source.id,
                    "feed_id": item.id,
                    "ical_url": item.ical_url,
                    "cf_challenges_so_far": cf_challenges,
                },
            )

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

        # Throttle between fetches to reduce Cloudflare challenge risk.
        if seen < len(items) and delay > 0:
            jitter = random.uniform(0, delay * 0.5)
            time.sleep(delay + jitter)

    logger.info(
        "Source feeds ingestion summary",
        extra={
            "source_id": source.id,
            "feeds_seen": seen,
            "events_ingested": ingested,
            "errors": errors,
            "cf_challenges": cf_challenges,
        },
    )

    if sink is not None:
        sink.flush()

    return {
        "feeds_seen": seen,
        "events_ingested": ingested,
        "errors": errors,
        "cf_challenges": cf_challenges,
    }
