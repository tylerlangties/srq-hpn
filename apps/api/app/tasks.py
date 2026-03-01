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
import os
import random
import time
from datetime import UTC, datetime
from typing import Any

import requests
from sqlalchemy import select

from app.celery_app import app
from app.db import SessionLocal
from app.models.source import Source
from app.services.ingest_sink import DbSink, MultiSink, ProdApiSink
from app.services.ingest_source_items import ingest_source_items
from app.services.weather_cache import (
    prune_old_weather_fetch_counters,
    prune_old_weather_reports,
    refresh_weather_cache,
)

logger = logging.getLogger(__name__)
WEATHER_REFRESH_JITTER_MAX_SECONDS = int(
    os.getenv("WEATHER_REFRESH_JITTER_MAX_SECONDS", "180")
)


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
def collect_vanwezel(
    self,
    source_id: int,
    delay: float = 0.5,
    future_only: bool = False,
) -> dict[str, Any]:
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

        stats = run_collector(db, source, delay=delay, future_only=future_only)
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
    self,
    source_id: int,
    delay: float = 0.5,
    months_ahead: int = 2,
    validate_ical: bool = False,
    future_only: bool = False,
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
            db,
            source,
            delay=delay,
            months_ahead=months_ahead,
            validate_ical=validate_ical,
            future_only=future_only,
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


@app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(requests.RequestException,),
)
def collect_asolorep(
    self,
    source_id: int,
    delay: float = 0.5,
    max_pages: int = 10,
    future_only: bool = False,
    validate_ical: bool = False,
    categories: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    from app.collectors.asolorep import run_collector

    logger.info(
        "Starting Asolo Rep collector task",
        extra={"source_id": source_id, "task_id": self.request.id},
    )

    db = SessionLocal()
    try:
        source = db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        stats = run_collector(
            db,
            source,
            delay=delay,
            max_pages=max_pages,
            future_only=future_only,
            validate_ical=validate_ical,
            categories=categories,
            dry_run=dry_run,
        )
        stats["task_id"] = self.request.id
        stats["started_at"] = datetime.now(UTC).isoformat()

        logger.info("Asolo Rep collector task completed", extra=stats)
        return stats

    except Exception as e:
        db.rollback()
        logger.error(
            "Asolo Rep collector task failed",
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
def collect_artfestival(
    self,
    source_id: int,
    delay: float = 0.5,
    max_pages: int = 10,
    validate_ical: bool = False,
    future_only: bool = False,
    categories: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    from app.collectors.artfestival import run_collector

    logger.info(
        "Starting ArtFestival collector task",
        extra={"source_id": source_id, "task_id": self.request.id},
    )

    db = SessionLocal()
    try:
        source = db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        stats = run_collector(
            db,
            source,
            delay=delay,
            max_pages=max_pages,
            validate_ical=validate_ical,
            future_only=future_only,
            categories=categories,
            dry_run=dry_run,
        )
        stats["task_id"] = self.request.id
        stats["started_at"] = datetime.now(UTC).isoformat()

        logger.info("ArtFestival collector task completed", extra=stats)
        return stats

    except Exception as e:
        db.rollback()
        logger.error(
            "ArtFestival collector task failed",
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
def collect_bigtop(
    self,
    source_id: int,
    delay: float = 0.25,
    max_pages: int = 10,
    validate_ical: bool = False,
    future_only: bool = False,
    created_months: int | None = None,
    categories: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    from app.collectors.bigtop import run_collector

    logger.info(
        "Starting Big Top collector task",
        extra={"source_id": source_id, "task_id": self.request.id},
    )

    db = SessionLocal()
    try:
        source = db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        stats = run_collector(
            db,
            source,
            delay=delay,
            max_pages=max_pages,
            validate_ical=validate_ical,
            future_only=future_only,
            created_months=created_months,
            categories=categories,
            dry_run=dry_run,
        )
        stats["task_id"] = self.request.id
        stats["started_at"] = datetime.now(UTC).isoformat()

        logger.info("Big Top collector task completed", extra=stats)
        return stats

    except Exception as e:
        db.rollback()
        logger.error(
            "Big Top collector task failed",
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
def collect_bigwaters(
    self,
    source_id: int,
    delay: float = 0.5,
    max_pages: int = 10,
    include_past: bool = False,
    future_only: bool | None = None,
    validate_ical: bool = False,
    categories: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    from app.collectors.bigwaters import run_collector

    logger.info(
        "Starting Big Waters collector task",
        extra={"source_id": source_id, "task_id": self.request.id},
    )

    db = SessionLocal()
    try:
        source = db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        stats = run_collector(
            db,
            source,
            delay=delay,
            max_pages=max_pages,
            include_past=include_past,
            future_only=future_only,
            validate_ical=validate_ical,
            categories=categories,
            dry_run=dry_run,
        )
        stats["task_id"] = self.request.id
        stats["started_at"] = datetime.now(UTC).isoformat()

        logger.info("Big Waters collector task completed", extra=stats)
        return stats

    except Exception as e:
        db.rollback()
        logger.error(
            "Big Waters collector task failed",
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
def collect_sarasotafair(
    self,
    source_id: int,
    delay: float = 0.5,
    max_days: int = 90,
    chunk_size: int = 10,
    max_pages: int = 10,
    validate_ical: bool = False,
    future_only: bool = False,
    categories: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    from app.collectors.sarasotafair import run_collector

    logger.info(
        "Starting Sarasota Fair collector task",
        extra={"source_id": source_id, "task_id": self.request.id},
    )

    db = SessionLocal()
    try:
        source = db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        stats = run_collector(
            db,
            source,
            delay=delay,
            max_days=max_days,
            chunk_size=chunk_size,
            max_pages=max_pages,
            validate_ical=validate_ical,
            future_only=future_only,
            categories=categories,
            dry_run=dry_run,
        )
        stats["task_id"] = self.request.id
        stats["started_at"] = datetime.now(UTC).isoformat()

        logger.info("Sarasota Fair collector task completed", extra=stats)
        return stats

    except Exception as e:
        db.rollback()
        logger.error(
            "Sarasota Fair collector task failed",
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
def collect_selby(
    self,
    source_id: int,
    delay: float = 0.5,
    max_pages: int = 50,
    filters: str | None = None,
    validate_ical: bool = False,
    future_only: bool = False,
    published_months: int | None = None,
    categories: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    from app.collectors.selby import run_collector

    logger.info(
        "Starting Selby collector task",
        extra={"source_id": source_id, "task_id": self.request.id},
    )

    db = SessionLocal()
    try:
        source = db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        stats = run_collector(
            db,
            source,
            delay=delay,
            max_pages=max_pages,
            filters=filters,
            validate_ical=validate_ical,
            future_only=future_only,
            published_months=published_months,
            categories=categories,
            dry_run=dry_run,
        )
        stats["task_id"] = self.request.id
        stats["started_at"] = datetime.now(UTC).isoformat()

        logger.info("Selby collector task completed", extra=stats)
        return stats

    except Exception as e:
        db.rollback()
        logger.error(
            "Selby collector task failed",
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
def sync_bigtop_local_bridge(
    self,
    source_id: int = 5,
    limit: int = 500,
    delay: float = 0.25,
    future_only: bool = True,
    created_months: int | None = None,
    categories: str | None = None,
    push_prod: bool = True,
    batch_size: int = 250,
    timeout_seconds: int = 30,
    retries: int = 3,
    dry_run: bool = False,
) -> dict[str, Any]:
    env = os.getenv("ENV", "development").strip().lower()
    if env == "production":
        raise RuntimeError("sync_bigtop_local_bridge is disabled in production")

    if limit < 1:
        raise ValueError("limit must be at least 1")

    if push_prod and not dry_run:
        api_base = os.getenv("BIGTOP_INGEST_API_BASE")
        token = os.getenv("BIGTOP_INGEST_TOKEN")
        if not api_base:
            raise ValueError("BIGTOP_INGEST_API_BASE is required when push_prod=true")
        if not token:
            raise ValueError("BIGTOP_INGEST_TOKEN is required when push_prod=true")
    else:
        api_base = None
        token = None

    from app.collectors.bigtop import run_collector

    logger.info(
        "Starting local Big Top bridge sync task",
        extra={
            "task_id": self.request.id,
            "source_id": source_id,
            "limit": limit,
            "future_only": future_only,
            "created_months": created_months,
            "push_prod": push_prod,
            "dry_run": dry_run,
        },
    )

    db = SessionLocal()
    try:
        source = db.get(Source, source_id)
        if source is None:
            raise ValueError(f"Source {source_id} not found")

        collector_stats = run_collector(
            db,
            source,
            delay=delay,
            future_only=future_only,
            created_months=created_months,
            categories=categories,
            dry_run=dry_run,
        )

        sink: DbSink | MultiSink = DbSink()
        prod_sink: ProdApiSink | None = None

        if push_prod and not dry_run and api_base and token:
            prod_sink = ProdApiSink(
                api_base=api_base,
                token=token,
                batch_size=batch_size,
                timeout_seconds=timeout_seconds,
                retries=retries,
            )
            sink = MultiSink([DbSink(), prod_sink])

        ingest_stats = ingest_source_items(
            db,
            source=source,
            limit=limit,
            delay=delay,
            sink=sink,
        )
        db.commit()

        result: dict[str, Any] = {
            "task_id": self.request.id,
            "source_id": source_id,
            "collector": collector_stats,
            "ingest": ingest_stats,
            "prod_push": {
                "enabled": bool(prod_sink),
                "run_id": prod_sink.run_id if prod_sink else None,
                "received": prod_sink.received if prod_sink else 0,
                "upserted": prod_sink.upserted if prod_sink else 0,
                "rejected": prod_sink.rejected if prod_sink else 0,
            },
        }

        logger.info("Local Big Top bridge sync task completed", extra=result)
        return result
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@app.task(bind=True)
def refresh_weather(self) -> dict[str, Any]:
    logger.info(
        "Starting weather cache refresh task", extra={"task_id": self.request.id}
    )

    db = SessionLocal()
    try:
        jitter_seconds = 0
        if WEATHER_REFRESH_JITTER_MAX_SECONDS > 0:
            jitter_seconds = random.randint(0, WEATHER_REFRESH_JITTER_MAX_SECONDS)
            if jitter_seconds > 0:
                logger.info(
                    "Applying weather refresh jitter",
                    extra={
                        "task_id": self.request.id,
                        "jitter_seconds": jitter_seconds,
                    },
                )
                time.sleep(jitter_seconds)

        result = refresh_weather_cache(db)
        logger.info(
            "Weather cache refresh task completed",
            extra={
                "task_id": self.request.id,
                "jitter_seconds": jitter_seconds,
                **result,
            },
        )
        return {
            "task_id": self.request.id,
            "status": "success",
            "jitter_seconds": jitter_seconds,
            **result,
        }
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


@app.task(bind=True)
def prune_weather_fetch_counters_task(self) -> dict[str, Any]:
    logger.info(
        "Starting weather fetch counter prune task", extra={"task_id": self.request.id}
    )

    db = SessionLocal()
    try:
        deleted_rows = prune_old_weather_fetch_counters(db)
        logger.info(
            "Weather fetch counter prune task completed",
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
            "Weather fetch counter prune task failed",
            extra={"task_id": self.request.id, "error": f"{type(exc).__name__}: {exc}"},
            exc_info=True,
        )
        raise
    finally:
        db.close()
