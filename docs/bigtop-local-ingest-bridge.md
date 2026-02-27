# Big Top Local-to-Prod Ingest Bridge

Temporary bridge for Big Top while production cannot fetch Big Top iCal URLs due to Cloudflare challenges.

## Overview

1. Local machine runs the existing Big Top collector to refresh source feeds.
2. Local machine runs the existing source-feed ingester (same local DB write path as normal).
3. During ingest, events fan out to the production endpoint in batches.
4. Production endpoint only upserts events for Big Top source and does not fetch external URLs.

## Production Setup

Set this env var for the API service:

- `BIGTOP_INGEST_TOKEN`: long random secret used by ingest bridge bearer auth.

Deploy API after setting env.

## Endpoint

- `POST /api/ingest/bigtop/events`
- Auth: `Authorization: Bearer <BIGTOP_INGEST_TOKEN>`

Request body fields:

- `source_id` (int): should be Big Top source id (default `5`)
- `run_id` (string): unique run identifier from local worker
- `sent_at` (ISO datetime with timezone)
- `events` (1..500 items)

Each event item:

- `external_id` (string, iCal UID)
- `title` (string)
- `start_utc` (ISO datetime with timezone)
- `description`, `location`, `end_utc`, `external_url` (optional)
- `categories` (optional list)

## Local Runner

Script:

- `apps/api/scripts/push_bigtop_from_local.py`

Required env or flags:

- `BIGTOP_INGEST_API_BASE` or `--api-base`
- `BIGTOP_INGEST_TOKEN` or `--token`

Example:

```bash
cd apps/api
PYTHONPATH=. python scripts/push_bigtop_from_local.py \
  --api-base https://srqhappenings.com \
  --token "$BIGTOP_INGEST_TOKEN" \
  --source-id 5 \
  --limit 200 \
  --batch-size 250
```

Dry run:

```bash
cd apps/api
PYTHONPATH=. python scripts/push_bigtop_from_local.py --dry-run
```

Local-only run (no prod push):

```bash
cd apps/api
PYTHONPATH=. python scripts/push_bigtop_from_local.py --no-push-prod
```

## Suggested Schedule

- Start with manual runs for 1-2 days.
- Then schedule via cron (every 6-12 hours is usually enough).

## Local Celery Task (Disabled in Prod)

Task name:

- `app.tasks.sync_bigtop_local_bridge`

This task hard-fails when `ENV=production`.

Manual task call example:

```bash
cd apps/api
PYTHONPATH=. .venv/bin/celery -A app.celery_app call app.tasks.sync_bigtop_local_bridge \
  --kwargs='{"source_id": 5, "limit": 200, "future_only": true, "delay": 1.0, "push_prod": true}'
```

Example cron:

```cron
0 */6 * * * cd /path/to/srq-hpn/apps/api && PYTHONPATH=. /path/to/venv/bin/python scripts/push_bigtop_from_local.py >> /var/log/bigtop-bridge.log 2>&1
```

## Rollback

1. Disable local cron job.
2. Rotate `BIGTOP_INGEST_TOKEN` in production.
3. Redeploy API env if needed.
