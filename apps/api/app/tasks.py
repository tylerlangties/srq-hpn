"""
Celery Task Definitions

This module contains all Celery tasks that can be executed by workers.
Tasks are decorated with @app.task to register them with Celery.

Task Types in this project:
1. Direct collectors: Collect events from websites and ingest directly (e.g., Van Wezel)
2. Source feed collectors: Discover iCal URLs and store them for later ingestion (e.g., Mote)
3. Ingestion tasks: Process source feeds and ingest events from iCal files

Each task:
- Runs in its own database session (isolated transactions)
- Has retry logic for transient failures
- Logs progress for monitoring

Note: The actual collection logic lives in app/collectors/. These tasks are thin
wrappers that provide Celery integration (retries, scheduling, result tracking).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import requests
from sqlalchemy import select

from app.celery_app import app
from app.db import SessionLocal
from app.models.source import Source
from app.services.ingest_source_items import ingest_source_items
from app.services.weather_cache import prune_old_weather_reports, refresh_weather_cache

logger = logging.getLogger(__name__)


# =============================================================================
# Direct Collector Tasks
# These collectors fetch data and ingest it directly into the database
# =============================================================================


@app.task(
    bind=True,  # Gives access to self (task instance) for retries
    max_retries=3,  # Maximum number of retry attempts
    default_retry_delay=60,  # Wait 60 seconds between retries
    autoretry_for=(requests.RequestException,),  # Auto-retry on network errors
)
def collect_vanwezel(self, source_id: int, delay: float = 0.5) -> dict[str, Any]:
    """
    Collect Van Wezel Performing Arts Hall events.

    This is a "direct" collector that:
    1. Fetches the events listing page
    2. Extracts event URLs
    3. Collects each event detail page
    4. Ingests events directly into the database

    Args:
        source_id: The database ID of the Van Wezel source
        delay: Seconds to wait between requests (be respectful to the server)

    Returns:
        Dictionary with collection statistics
    """
    from app.collectors.vanwezel import run_collector

    logger.info(
        "Starting Van Wezel collector task",
        extra={"source_id": source_id, "task_id": self.request.id},
    )

    db = SessionLocal()
    try:
        source = db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        stats = run_collector(db, source, delay=delay)
        stats["task_id"] = self.request.id
        stats["started_at"] = datetime.now(UTC).isoformat()

        logger.info("Van Wezel collector task completed", extra=stats)
        return stats

    except Exception as e:
        db.rollback()
        logger.error(
            "Van Wezel collector task failed",
            extra={"source_id": source_id, "error": str(e)},
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
def collect_mote(
    self, source_id: int, months_ahead: int = 2, validate_ical: bool = False
) -> dict[str, Any]:
    """
    Collect Mote Marine monthly iCal feeds.

    This is a "source feed" collector that:
    1. Generates iCal URLs for current and future months
    2. Stores these URLs in the source_feeds table
    3. The feeds are later ingested by ingest_source_items()

    Args:
        source_id: The database ID of the Mote Marine source
        months_ahead: Number of future months to include (default: 2)
        validate_ical: Whether to validate iCal URLs are accessible

    Returns:
        Dictionary with collection statistics
    """
    from app.collectors.mote import run_collector

    logger.info(
        "Starting Mote Marine collector task",
        extra={"source_id": source_id, "task_id": self.request.id},
    )

    db = SessionLocal()
    try:
        source = db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        stats = run_collector(
            db, source, months_ahead=months_ahead, validate_ical=validate_ical
        )
        stats["task_id"] = self.request.id
        stats["started_at"] = datetime.now(UTC).isoformat()

        logger.info("Mote Marine collector task completed", extra=stats)
        return stats

    except Exception as e:
        db.rollback()
        logger.error(
            "Mote Marine collector task failed",
            extra={"source_id": source_id, "error": str(e)},
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


@app.task(bind=True)
def refresh_weather(self) -> dict[str, Any]:
    logger.info(
        "Starting weather cache refresh task", extra={"task_id": self.request.id}
    )

    db = SessionLocal()
    try:
        result = refresh_weather_cache(db)
        logger.info(
            "Weather cache refresh task completed",
            extra={"task_id": self.request.id, **result},
        )
        return {"task_id": self.request.id, "status": "success", **result}
    except Exception as exc:
        db.rollback()
        logger.error(
            "Weather cache refresh task failed",
            extra={"task_id": self.request.id, "error": f"{type(exc).__name__}: {exc}"},
            exc_info=True,
        )
        raise
    finally:
        db.close()


@app.task(bind=True)
def prune_weather_reports(self) -> dict[str, Any]:
    logger.info(
        "Starting weather report prune task", extra={"task_id": self.request.id}
    )

    db = SessionLocal()
    try:
        deleted_rows = prune_old_weather_reports(db)
        logger.info(
            "Weather report prune task completed",
            extra={"task_id": self.request.id, "deleted_rows": deleted_rows},
        )
        return {
            "task_id": self.request.id,
            "status": "success",
            "deleted_rows": deleted_rows,
        }
    except Exception as exc:
        db.rollback()
        logger.error(
            "Weather report prune task failed",
            extra={"task_id": self.request.id, "error": f"{type(exc).__name__}: {exc}"},
            exc_info=True,
        )
        raise
    finally:
        db.close()
