# Celery Background Tasks Guide

This guide explains how Celery is set up in this project for automated scraping and background task processing.

## Table of Contents

- [What is Celery?](#what-is-celery)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Running Tasks](#running-tasks)
- [Monitoring with Flower](#monitoring-with-flower)
- [Configuration](#configuration)
- [Adding New Tasks](#adding-new-tasks)
- [Command Reference](#command-reference)
- [Troubleshooting](#troubleshooting)

---

## What is Celery?

Celery is a **distributed task queue** that allows you to run code in the background, separate from your main web application. Think of it like a to-do list for your application:

1. Your app adds a task to the list (e.g., "scrape Van Wezel website")
2. A worker picks up the task and executes it
3. The result is stored for later retrieval

### Key Benefits

- **Non-blocking**: Long-running tasks (like web scraping) don't slow down your API
- **Scheduled tasks**: Run scrapers automatically at specific times (like cron jobs)
- **Reliability**: Failed tasks can be retried automatically
- **Scalability**: Add more workers to process tasks faster

### Core Components

| Component | Description |
|-----------|-------------|
| **Broker** | Message queue that stores tasks (we use Redis) |
| **Worker** | Process that executes tasks from the queue |
| **Beat** | Scheduler that sends periodic tasks to the queue |
| **Backend** | Storage for task results (we use Redis) |

---

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│    Redis    │◀────│   Worker    │
│    (API)    │     │  (Broker)   │     │ (Executor)  │
└─────────────┘     └─────────────┘     └─────────────┘
                           ▲
                           │
                    ┌──────┴──────┐
                    │    Beat     │
                    │ (Scheduler) │
                    └─────────────┘
```

**Flow:**
1. **Beat** checks its schedule and sends tasks to Redis at configured times
2. **Redis** queues the tasks until a worker is available
3. **Worker** picks up tasks, executes them, and stores results in Redis
4. **API** can also send tasks directly to Redis (for on-demand execution)

---

## Quick Start

### Starting All Services

```bash
# Start all services (including Celery)
docker compose -f compose.dev.yml up
```

This starts:
- PostgreSQL database (port 5432)
- Redis message broker (port 6379)
- FastAPI server (port 8000)
- Celery worker (background tasks)
- Celery beat (task scheduler)
- Flower monitoring (port 5555)
- Next.js frontend (port 3000)

### Starting Individual Services

```bash
# Start only the background task infrastructure
docker compose -f compose.dev.yml up redis celery-worker celery-beat flower

# Start worker only (useful for development/debugging)
docker compose -f compose.dev.yml up celery-worker
```

### Viewing Logs

```bash
# View all Celery-related logs
docker compose -f compose.dev.yml logs -f celery-worker celery-beat

# View only worker logs
docker compose -f compose.dev.yml logs -f celery-worker

# View only scheduler logs
docker compose -f compose.dev.yml logs -f celery-beat
```

**Flags explained:**
- `-f` (follow): Stream logs in real-time (like `tail -f`)

---

## Running Tasks

### Automatic (Scheduled) Tasks

Tasks run automatically based on the schedule in `apps/api/app/celery_app.py`:

```python
app.conf.beat_schedule = {
    "scrape-vanwezel-daily": {
        "task": "app.tasks.scrape_vanwezel",
        "schedule": crontab(minute=0, hour=6),  # 6:00 AM daily
        "kwargs": {"source_id": 1},
    },
}
```

### Manual Task Execution

You can run tasks manually using the Celery CLI or Python shell.

#### Method 1: Docker Exec into Worker

```bash
# Open a shell in the worker container
docker compose -f compose.dev.yml exec celery-worker bash

# Then run Python to trigger a task
python -c "from app.tasks import scrape_vanwezel; scrape_vanwezel.delay(source_id=1)"
```

#### Method 2: Using Celery CLI

```bash
# Run a task by name
docker compose -f compose.dev.yml exec celery-worker \
  celery -A app.celery_app call app.tasks.scrape_vanwezel --kwargs='{"source_id": 1}'
```

**Flags explained:**
- `-A app.celery_app`: Specifies the Celery application module
- `call`: Celery subcommand to execute a task
- `--kwargs`: JSON object of keyword arguments to pass to the task

#### Method 3: From the API

You can also trigger tasks from your FastAPI code:

```python
from app.tasks import scrape_vanwezel

# Send task to queue (returns immediately)
result = scrape_vanwezel.delay(source_id=1)

# Get the task ID
print(f"Task ID: {result.id}")

# Check if task is complete (non-blocking)
print(f"Ready: {result.ready()}")

# Wait for and get the result (blocking)
print(f"Result: {result.get(timeout=300)}")
```

### Available Tasks

| Task | Description | Arguments |
|------|-------------|-----------|
| `scrape_vanwezel` | Scrapes Van Wezel events directly | `source_id`, `delay=0.5` |
| `scrape_mote` | Discovers Mote Marine iCal feeds | `source_id`, `months_ahead=2` |
| `ingest_source` | Ingests feeds for one source | `source_id`, `limit=100` |
| `ingest_all_sources` | Ingests feeds for all sources | `limit_per_source=100` |
| `health_check` | Verifies Celery is working | (none) |

---

## Monitoring with Flower

Flower is a web-based monitoring tool for Celery. Access it at:

**http://localhost:5555**

### Features

- **Dashboard**: Overview of all workers and their status
- **Tasks**: View active, pending, succeeded, and failed tasks
- **Task Details**: Click any task to see arguments, result, and traceback
- **Worker Control**: Restart workers, adjust concurrency
- **API**: REST API for programmatic monitoring

### Common Flower Operations

1. **View task history**: Tasks tab → filter by state or name
2. **Inspect a failed task**: Click the task → view traceback
3. **Monitor queue depth**: Dashboard → shows pending task count
4. **Check worker health**: Workers tab → green = healthy

---

## Configuration

### Celery Configuration (`apps/api/app/celery_app.py`)

```python
# Redis connection (broker and result backend)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app.conf.update(
    # Task serialization
    task_serializer="json",      # Tasks are serialized as JSON
    result_serializer="json",    # Results stored as JSON
    accept_content=["json"],     # Only accept JSON (security)
    
    # Timezone
    timezone="America/New_York", # Schedule times in Eastern
    enable_utc=True,             # Store internally as UTC
    
    # Result storage
    result_expires=3600,         # Delete results after 1 hour
    
    # Task execution
    task_acks_late=True,         # Ack after completion (not receipt)
    task_reject_on_worker_lost=True,  # Requeue if worker dies
    
    # Worker settings
    worker_prefetch_multiplier=1,     # Fetch 1 task at a time
    worker_concurrency=2,             # 2 concurrent worker processes
)
```

### Schedule Configuration

The schedule uses crontab syntax:

```python
from celery.schedules import crontab

# crontab(minute, hour, day_of_week, day_of_month, month_of_year)

crontab(minute=0, hour=6)                    # Daily at 6:00 AM
crontab(minute="*/15")                        # Every 15 minutes
crontab(minute=0, hour="*/2")                 # Every 2 hours
crontab(minute=0, hour=8, day_of_week="mon")  # Mondays at 8 AM
crontab(minute=30, hour=6, day_of_month=1)    # 1st of month at 6:30 AM
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `DATABASE_URL` | PostgreSQL connection (for workers) | (required) |

---

## Adding New Tasks

### Step 1: Create the Task Function

Add to `apps/api/app/tasks.py`:

```python
@app.task(
    bind=True,                    # Access to self for retries
    max_retries=3,                # Retry up to 3 times
    default_retry_delay=60,       # Wait 60s between retries
    autoretry_for=(RequestException,),  # Auto-retry on these errors
)
def my_new_scraper(self, source_id: int) -> dict:
    """
    Description of what this scraper does.
    
    Args:
        source_id: Database ID of the source
        
    Returns:
        Dictionary with scraping statistics
    """
    # Your scraping logic here
    return {"status": "success", "items_scraped": 42}
```

### Step 2: Add to Schedule (Optional)

Add to `apps/api/app/celery_app.py`:

```python
app.conf.beat_schedule = {
    # ... existing tasks ...
    
    "my-new-scraper-daily": {
        "task": "app.tasks.my_new_scraper",
        "schedule": crontab(minute=0, hour=7),  # 7:00 AM daily
        "kwargs": {"source_id": 5},
    },
}
```

### Step 3: Restart Beat

```bash
docker compose -f compose.dev.yml restart celery-beat
```

---

## Command Reference

### Docker Compose Commands

```bash
# Start all services
docker compose -f compose.dev.yml up

# Start in background (detached)
docker compose -f compose.dev.yml up -d

# Stop all services
docker compose -f compose.dev.yml down

# Restart a specific service
docker compose -f compose.dev.yml restart celery-worker

# View logs
docker compose -f compose.dev.yml logs -f celery-worker

# Execute command in container
docker compose -f compose.dev.yml exec celery-worker <command>
```

**Flags explained:**
- `-f compose.dev.yml`: Specifies which compose file to use
- `-d` (detach): Run in background, return control to terminal
- `-f` (with logs): Follow/stream log output continuously

### Celery CLI Commands

All commands should be run inside a container:

```bash
# First, enter the worker container
docker compose -f compose.dev.yml exec celery-worker bash

# Then run Celery commands:
```

```bash
# Check worker status
celery -A app.celery_app inspect active

# List registered tasks
celery -A app.celery_app inspect registered

# View task result by ID
celery -A app.celery_app result <task-id>

# Purge all pending tasks (careful!)
celery -A app.celery_app purge

# Run a task immediately
celery -A app.celery_app call app.tasks.health_check
```

**Flags explained:**
- `-A app.celery_app`: Application module path (required for all commands)
- `inspect`: Subcommand to query worker state
- `active`: Shows currently executing tasks
- `registered`: Shows all available task names

### Useful Task Execution Commands

```bash
# Run health check (test Celery is working)
docker compose -f compose.dev.yml exec celery-worker \
  celery -A app.celery_app call app.tasks.health_check

# Manually trigger Van Wezel scraper
docker compose -f compose.dev.yml exec celery-worker \
  celery -A app.celery_app call app.tasks.scrape_vanwezel \
  --kwargs='{"source_id": 1}'

# Manually trigger Mote Marine scraper
docker compose -f compose.dev.yml exec celery-worker \
  celery -A app.celery_app call app.tasks.scrape_mote \
  --kwargs='{"source_id": 2}'

# Ingest all source feeds
docker compose -f compose.dev.yml exec celery-worker \
  celery -A app.celery_app call app.tasks.ingest_all_sources
```

---

## Troubleshooting

### Common Issues

#### Tasks Not Running

1. **Check worker is running:**
   ```bash
   docker compose -f compose.dev.yml ps celery-worker
   ```

2. **Check worker logs for errors:**
   ```bash
   docker compose -f compose.dev.yml logs celery-worker
   ```

3. **Verify Redis is accessible:**
   ```bash
   docker compose -f compose.dev.yml exec redis redis-cli ping
   # Should return: PONG
   ```

#### Scheduled Tasks Not Triggering

1. **Check beat is running:**
   ```bash
   docker compose -f compose.dev.yml ps celery-beat
   ```

2. **Check beat logs:**
   ```bash
   docker compose -f compose.dev.yml logs celery-beat
   ```

3. **Verify schedule configuration:**
   - Check `apps/api/app/celery_app.py` for `beat_schedule`
   - Ensure task names match exactly

#### Worker Crashes / Out of Memory

1. **Reduce concurrency:**
   Edit `compose.dev.yml`, change:
   ```yaml
   command: celery -A app.celery_app worker --loglevel=INFO --concurrency=1
   ```

2. **Check for memory leaks in tasks:**
   - Ensure database sessions are closed
   - Don't store large objects in memory

#### Tasks Stuck in Pending

1. **Check queue depth:**
   - Open Flower (http://localhost:5555)
   - Dashboard shows pending count

2. **Check if worker is consuming:**
   ```bash
   docker compose -f compose.dev.yml exec celery-worker \
     celery -A app.celery_app inspect active
   ```

3. **Purge stuck tasks (last resort):**
   ```bash
   docker compose -f compose.dev.yml exec celery-worker \
     celery -A app.celery_app purge
   ```

### Debugging Tasks

#### View Task Result

```bash
# Get task ID from Flower or logs, then:
docker compose -f compose.dev.yml exec celery-worker \
  celery -A app.celery_app result <task-id>
```

#### Enable Debug Logging

Edit `compose.dev.yml`, change worker command:

```yaml
command: celery -A app.celery_app worker --loglevel=DEBUG --concurrency=2
```

#### Test Task in Python Shell

```bash
docker compose -f compose.dev.yml exec celery-worker python

>>> from app.tasks import health_check
>>> result = health_check.delay()
>>> print(result.get(timeout=10))
```

---

## Best Practices

1. **Keep tasks small and focused** - One task, one job
2. **Make tasks idempotent** - Running twice should be safe
3. **Use database transactions** - Commit at the end, rollback on error
4. **Add retry logic** - Network requests can fail
5. **Log progress** - Helps debugging and monitoring
6. **Set timeouts** - Prevent tasks from running forever
7. **Test tasks manually first** - Before adding to schedule

---

## Further Reading

- [Celery Documentation](https://docs.celeryq.dev/)
- [Celery Best Practices](https://docs.celeryq.dev/en/stable/userguide/tasks.html#tips-and-best-practices)
- [Flower Documentation](https://flower.readthedocs.io/)
- [Redis Documentation](https://redis.io/docs/)
