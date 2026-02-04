"""
Celery Task Definitions

This module contains all Celery tasks that can be executed by workers.
Tasks are decorated with @app.task to register them with Celery.

Task Types in this project:
1. Direct scrapers: Scrape websites and ingest events directly (e.g., Van Wezel)
2. Source feed scrapers: Discover iCal URLs and store them for later ingestion (e.g., Mote)
3. Ingestion tasks: Process source feeds and ingest events from iCal files

Each task:
- Runs in its own database session (isolated transactions)
- Has retry logic for transient failures
- Logs progress for monitoring
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from sqlalchemy import select
from urllib3.util.retry import Retry

from app.celery_app import app
from app.db import SessionLocal
from app.models.source import Source
from app.services.ingest_source_items import ingest_source_items

logger = logging.getLogger(__name__)


# =============================================================================
# Helper Functions
# =============================================================================


def get_http_session() -> requests.Session:
    """Create an HTTP session with retry logic."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


# =============================================================================
# Direct Scraper Tasks
# These scrapers fetch data and ingest it directly into the database
# =============================================================================


@app.task(
    bind=True,  # Gives access to self (task instance) for retries
    max_retries=3,  # Maximum number of retry attempts
    default_retry_delay=60,  # Wait 60 seconds between retries
    autoretry_for=(requests.RequestException,),  # Auto-retry on network errors
)
def scrape_vanwezel(self, source_id: int, delay: float = 0.5) -> dict[str, Any]:
    """
    Scrape Van Wezel Performing Arts Hall events.

    This is a "direct" scraper that:
    1. Fetches the events listing page
    2. Extracts event URLs
    3. Scrapes each event detail page
    4. Ingests events directly into the database

    Args:
        source_id: The database ID of the Van Wezel source
        delay: Seconds to wait between requests (be respectful to the server)

    Returns:
        Dictionary with scraping statistics
    """
    # Import here to avoid circular imports
    # Note: scripts/ is a sibling directory to app/, so we import from scripts.*
    from scripts.scrape_vanwezel import (
        EVENTS_URL,
        extract_event_links,
        fetch_html,
        ingest_event,
        scrape_event_detail,
    )

    logger.info(
        "Starting Van Wezel scraper task",
        extra={"source_id": source_id, "task_id": self.request.id},
    )

    stats = {
        "task_id": self.request.id,
        "source_id": source_id,
        "started_at": datetime.now(UTC).isoformat(),
        "events_discovered": 0,
        "events_scraped": 0,
        "events_failed": 0,
        "occurrences_created": 0,
        "errors": 0,
    }

    db = SessionLocal()
    session = get_http_session()

    try:
        source = db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        # Fetch event listing
        html = fetch_html(session, EVENTS_URL)
        event_links = extract_event_links(html)
        stats["events_discovered"] = len(event_links)

        # Deduplicate by URL
        seen_urls: set[str] = set()
        unique_events = []
        for event_link in event_links:
            if event_link["url"] not in seen_urls:
                seen_urls.add(event_link["url"])
                unique_events.append(event_link)

        # Scrape each event
        for event_link in unique_events:
            try:
                event = scrape_event_detail(session, event_link["url"])
                if event:
                    stats["events_scraped"] += 1
                    occurrences = ingest_event(db, source=source, event=event)
                    stats["occurrences_created"] += occurrences
                else:
                    stats["events_failed"] += 1

                time.sleep(delay)

            except Exception as e:
                stats["errors"] += 1
                stats["events_failed"] += 1
                logger.error(
                    "Failed to scrape event",
                    extra={
                        "url": event_link["url"],
                        "error_type": type(e).__name__,
                        "error": str(e),
                    },
                    exc_info=True,
                )

        db.commit()
        stats["completed_at"] = datetime.now(UTC).isoformat()
        stats["status"] = "success"

        logger.info(
            "Van Wezel scraper task completed",
            extra=stats,
        )

        return stats

    except Exception as e:
        db.rollback()
        stats["status"] = "error"
        stats["error"] = f"{type(e).__name__}: {e}"
        logger.error(
            "Van Wezel scraper task failed",
            extra=stats,
            exc_info=True,
        )
        raise

    finally:
        db.close()


@app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(requests.RequestException,),
)
def scrape_mote(
    self, source_id: int, months_ahead: int = 2, validate_ical: bool = False
) -> dict[str, Any]:
    """
    Scrape Mote Marine monthly iCal feeds.

    This is a "source feed" scraper that:
    1. Generates iCal URLs for current and future months
    2. Stores these URLs in the source_feeds table
    3. The feeds are later ingested by ingest_source_items()

    Args:
        source_id: The database ID of the Mote Marine source
        months_ahead: Number of future months to include (default: 2)
        validate_ical: Whether to validate iCal URLs are accessible

    Returns:
        Dictionary with scraping statistics
    """
    # Import here to avoid circular imports
    # Note: scripts/ is a sibling directory to app/, so we import from scripts.*
    from scripts.scrape_mote import (
        generate_month_entries,
        upsert_item,
        validate_ical_url,
    )

    logger.info(
        "Starting Mote Marine scraper task",
        extra={
            "source_id": source_id,
            "months_ahead": months_ahead,
            "task_id": self.request.id,
        },
    )

    stats = {
        "task_id": self.request.id,
        "source_id": source_id,
        "started_at": datetime.now(UTC).isoformat(),
        "feeds_considered": 0,
        "feeds_upserted": 0,
        "ical_validated": 0,
        "ical_invalid": 0,
        "errors": 0,
    }

    db = SessionLocal()
    session = get_http_session()

    try:
        source = db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        entries = generate_month_entries(months_ahead=months_ahead)

        for entry in entries:
            stats["feeds_considered"] += 1
            try:
                if validate_ical:
                    if validate_ical_url(entry.ical_url, session):
                        stats["ical_validated"] += 1
                    else:
                        stats["ical_invalid"] += 1
                        continue

                upsert_item(db, source_id=source.id, entry=entry)
                stats["feeds_upserted"] += 1

            except Exception as e:
                stats["errors"] += 1
                logger.error(
                    "Error upserting month entry",
                    extra={
                        "source_id": source.id,
                        "year_month": entry.year_month,
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )

        db.commit()
        stats["completed_at"] = datetime.now(UTC).isoformat()
        stats["status"] = "success"

        logger.info(
            "Mote Marine scraper task completed",
            extra=stats,
        )

        return stats

    except Exception as e:
        db.rollback()
        stats["status"] = "error"
        stats["error"] = f"{type(e).__name__}: {e}"
        logger.error(
            "Mote Marine scraper task failed",
            extra=stats,
            exc_info=True,
        )
        raise

    finally:
        db.close()


# =============================================================================
# Ingestion Tasks
# These tasks process source feeds (iCal URLs) and ingest events
# =============================================================================


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def ingest_source(self, source_id: int, limit: int = 100) -> dict[str, Any]:
    """
    Ingest events from source feeds for a specific source.

    This task:
    1. Fetches all source_feeds for the given source
    2. Downloads and parses each iCal file
    3. Upserts events into the database

    Args:
        source_id: The database ID of the source to ingest
        limit: Maximum number of feeds to process

    Returns:
        Dictionary with ingestion statistics
    """
    logger.info(
        "Starting source ingestion task",
        extra={"source_id": source_id, "limit": limit, "task_id": self.request.id},
    )

    stats = {
        "task_id": self.request.id,
        "source_id": source_id,
        "started_at": datetime.now(UTC).isoformat(),
    }

    db = SessionLocal()

    try:
        source = db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        result = ingest_source_items(db, source=source, limit=limit)
        db.commit()

        stats.update(result)
        stats["completed_at"] = datetime.now(UTC).isoformat()
        stats["status"] = "success"

        logger.info(
            "Source ingestion task completed",
            extra=stats,
        )

        return stats

    except Exception as e:
        db.rollback()
        stats["status"] = "error"
        stats["error"] = f"{type(e).__name__}: {e}"
        logger.error(
            "Source ingestion task failed",
            extra=stats,
            exc_info=True,
        )
        raise

    finally:
        db.close()


@app.task(bind=True)
def ingest_all_sources(self, limit_per_source: int = 100) -> dict[str, Any]:
    """
    Ingest events from all sources that have source feeds.

    This is a convenience task that runs ingest_source for each source.
    Useful for scheduled daily ingestion of all iCal-based sources.

    Args:
        limit_per_source: Maximum feeds to process per source

    Returns:
        Dictionary with aggregated ingestion statistics
    """
    logger.info(
        "Starting all-sources ingestion task",
        extra={"limit_per_source": limit_per_source, "task_id": self.request.id},
    )

    stats = {
        "task_id": self.request.id,
        "started_at": datetime.now(UTC).isoformat(),
        "sources_processed": 0,
        "total_feeds_seen": 0,
        "total_events_ingested": 0,
        "total_errors": 0,
        "source_results": [],
    }

    db = SessionLocal()

    try:
        # Get all active sources
        sources = db.scalars(select(Source)).all()

        for source in sources:
            try:
                result = ingest_source_items(db, source=source, limit=limit_per_source)
                db.commit()

                stats["sources_processed"] += 1
                stats["total_feeds_seen"] += result["feeds_seen"]
                stats["total_events_ingested"] += result["events_ingested"]
                stats["total_errors"] += result["errors"]
                stats["source_results"].append(
                    {
                        "source_id": source.id,
                        "source_name": source.name,
                        **result,
                    }
                )

            except Exception as e:
                db.rollback()
                stats["total_errors"] += 1
                stats["source_results"].append(
                    {
                        "source_id": source.id,
                        "source_name": source.name,
                        "status": "error",
                        "error": f"{type(e).__name__}: {e}",
                    }
                )
                logger.error(
                    "Failed to ingest source",
                    extra={
                        "source_id": source.id,
                        "source_name": source.name,
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )

        stats["completed_at"] = datetime.now(UTC).isoformat()
        stats["status"] = "success"

        logger.info(
            "All-sources ingestion task completed",
            extra={
                "sources_processed": stats["sources_processed"],
                "total_events_ingested": stats["total_events_ingested"],
                "total_errors": stats["total_errors"],
            },
        )

        return stats

    except Exception as e:
        stats["status"] = "error"
        stats["error"] = f"{type(e).__name__}: {e}"
        logger.error(
            "All-sources ingestion task failed",
            extra=stats,
            exc_info=True,
        )
        raise

    finally:
        db.close()


# =============================================================================
# Utility Tasks
# =============================================================================


@app.task
def health_check() -> dict[str, Any]:
    """
    Simple health check task to verify Celery is working.

    Returns:
        Dictionary with health status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "message": "Celery worker is running",
    }
