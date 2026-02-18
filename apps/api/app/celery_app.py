"""
Celery Application Configuration

This module configures Celery for background task processing.
Celery uses Redis as both the message broker (task queue) and result backend.

Key concepts:
- Broker: Where tasks are sent to be picked up by workers (Redis)
- Backend: Where task results are stored (Redis)
- Worker: A process that executes tasks from the queue
- Beat: A scheduler that sends tasks to the queue at specified intervals
"""

from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

# Redis connection URL - defaults to local Redis for development
# In Docker, this will be redis://redis:6379/0
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create the Celery application instance
# The first argument is the name of the current module (used for auto-generating task names)
app = Celery(
    "srq_hpn",
    broker=REDIS_URL,
    backend=REDIS_URL,
    # Tell Celery where to find task definitions
    include=["app.tasks"],
)

# Celery configuration
# See: https://docs.celeryq.dev/en/stable/userguide/configuration.html
app.conf.update(
    # Task settings
    task_serializer="json",  # How tasks are serialized when sent to the broker
    result_serializer="json",  # How results are serialized when stored
    accept_content=["json"],  # Only accept JSON content (security)
    # Timezone settings
    timezone="America/New_York",  # Use Eastern time for scheduling
    enable_utc=True,  # Store times in UTC internally
    # Result settings
    result_expires=604800,  # Results expire after 7 days (in seconds)
    # Task execution settings
    task_acks_late=True,  # Acknowledge task after it completes (not when received)
    task_reject_on_worker_lost=True,  # Requeue task if worker dies unexpectedly
    # Worker settings
    worker_prefetch_multiplier=1,  # Only fetch 1 task at a time (good for long tasks)
    worker_concurrency=2,  # Number of concurrent worker processes
    # Beat scheduler settings (for periodic tasks)
    beat_scheduler="celery.beat:PersistentScheduler",
    beat_schedule_filename="/tmp/celerybeat-schedule",  # Where beat stores its schedule
)

# =============================================================================
# Periodic Task Schedule (Celery Beat)
# =============================================================================
#
# This defines which tasks run automatically and when.
# Celery Beat acts as a cron-like scheduler that sends tasks to the queue.
#
# Schedule options:
# - crontab(minute, hour, day_of_week, day_of_month, month_of_year)
# - timedelta(seconds=N) for interval-based scheduling
#
# Examples:
# - crontab(minute=0, hour=6)        -> Every day at 6:00 AM
# - crontab(minute="*/15")           -> Every 15 minutes
# - crontab(minute=0, hour="*/2")    -> Every 2 hours
# - crontab(minute=0, hour=8, day_of_week="mon")  -> Every Monday at 8 AM
# =============================================================================

app.conf.beat_schedule = {
    # ---------------------------------------------------------------------
    # Scraper Tasks
    # These tasks scrape external websites for event data
    # ---------------------------------------------------------------------
    # Van Wezel: Direct scraper (scrapes HTML, ingests directly)
    # Runs daily at 6:00 AM Eastern
    "collect-vanwezel-daily": {
        "task": "app.tasks.collect_vanwezel",
        "schedule": crontab(minute="0", hour="6"),
        "kwargs": {
            "source_id": 1,
            "future_only": True,
            "delay": 5.0,
        },
    },
    # Mote Marine: Source feed scraper (discovers iCal URLs)
    # Runs daily at 6:15 AM Eastern
    "collect-mote-daily": {
        "task": "app.tasks.collect_mote",
        "schedule": crontab(minute="15", hour="6"),
        "kwargs": {
            "source_id": 2,
            "future_only": True,
        },
    },
    "collect-asolorep-daily": {
        "task": "app.tasks.collect_asolorep",
        "schedule": crontab(minute="0", hour="5"),
        "kwargs": {
            "source_id": 3,
            "future_only": True,
            "delay": 5.0,
        },
    },
    "collect-artfestival-daily": {
        "task": "app.tasks.collect_artfestival",
        "schedule": crontab(minute="15", hour="5"),
        "kwargs": {
            "source_id": 4,
            "future_only": True,
            "delay": 5.0,
        },
    },
    "collect-bigtop-daily": {
        "task": "app.tasks.collect_bigtop",
        "schedule": crontab(minute="30", hour="5"),
        "kwargs": {
            "source_id": 5,
            "future_only": True,
            "delay": 5.0,
        },
    },
    "collect-bigwaters-daily": {
        "task": "app.tasks.collect_bigwaters",
        "schedule": crontab(minute="45", hour="5"),
        "kwargs": {
            "source_id": 6,
            "future_only": True,
            "delay": 5.0,
        },
    },
    "collect-sarasotafair-daily": {
        "task": "app.tasks.collect_sarasotafair",
        "schedule": crontab(minute="0", hour="6"),
        "kwargs": {
            "source_id": 7,
            "future_only": True,
            "delay": 5.0,
        },
    },
    "collect-selby-daily": {
        "task": "app.tasks.collect_selby",
        "schedule": crontab(minute="10", hour="6"),
        "kwargs": {
            "source_id": 8,
            "future_only": True,
            "delay": 5.0,
        },
    },
    # ---------------------------------------------------------------------
    # Ingestion Tasks
    # These tasks process source feeds that were discovered by scrapers
    # ---------------------------------------------------------------------
    # Ingest all source feeds (for sources that use iCal feeds)
    # Runs daily at 6:30 AM Eastern (after scrapers have discovered new feeds)
    "ingest-all-sources-daily": {
        "task": "app.tasks.ingest_all_sources",
        "schedule": crontab(minute="30", hour="6"),
    },
    # ---------------------------------------------------------------------
    # Weather Cache Tasks
    # ---------------------------------------------------------------------
    # Refresh weather cache every 6 hours to keep forecast reasonably current
    # while staying under free-tier API limits. Task-level jitter spreads calls.
    "refresh-weather-cache": {
        "task": "app.tasks.refresh_weather",
        "schedule": crontab(minute="5", hour="*/6"),
    },
    # Prune weather snapshots beyond retention window.
    "prune-weather-reports": {
        "task": "app.tasks.prune_weather_reports",
        "schedule": crontab(minute="20", hour="2"),
    },
    # Prune weather fetch counters to keep guardrail tracking table compact.
    "prune-weather-fetch-counters": {
        "task": "app.tasks.prune_weather_fetch_counters_task",
        "schedule": crontab(minute="40", hour="2"),
    },
}


# This allows running: celery -A app.celery_app worker
if __name__ == "__main__":
    app.start()
