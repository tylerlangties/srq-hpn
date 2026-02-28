# SRQ Happenings Deployment Plan (Single DigitalOcean Droplet)

Last updated: 2026-02-17

## 1) Goal and Scope

This plan defines a production deployment path for SRQ Happenings on one DigitalOcean Droplet, aligned to Step 5 in `docs/roadmap.md`.

It includes:

- Repeatable deployment workflow
- Production background jobs parity (Redis + Celery worker + Celery beat)
- Environment variable inventory from code + compose
- Security hardening checklist for DigitalOcean and host OS
- Runbook procedures (deploy, verify, rollback, backup, restore)

## 2) Current State and Gaps (from repo audit)

### What already exists

- Production compose stack with Caddy/Web/API/DB/Redis/Celery: `compose.yml`
- Reverse proxy + HTTPS config: `caddy/Caddyfile`
- DB/runbook guidance: `docs/database-guide.md`
- Celery architecture and operations guidance: `docs/celery-guide.md`
- Logging guidance: `docs/logging.md`

### Step 5 gaps to close

- Production jobs parity is implemented in `compose.yml` (`redis`, `celery-worker`, `celery-beat` are present)
- CI/CD workflows are not present (`.github/workflows` currently missing)
- Launch runbook needs one consolidated DO-droplet-specific plan

### Important config risk found

`apps/api/app/core/auth.py` requires `JWT_SECRET`. `compose.yml` now enforces this at compose render/runtime (`JWT_SECRET: ${JWT_SECRET:?JWT_SECRET is required}`), so startup is protected as long as `.env.production` provides a real secret.

## 3) Target Production Architecture (single Droplet)

```
Internet
  -> Caddy (80/443, TLS, routing)
    -> Web (Next.js, internal)
    -> API (FastAPI, internal)
      -> PostgreSQL (internal)
      -> Redis (internal)
      -> Celery Worker (internal)
      -> Celery Beat (internal, exactly one instance)
```

Guiding principle: expose only 80/443 publicly.

## 4) Deployment Strategy

Use Docker Compose on one Droplet for v1 launch.

### Recommended service set (production)

- `caddy`
- `web`
- `api`
- `db`
- `redis`
- `celery-worker`
- `celery-beat`

Optional later:

- `flower` behind auth and restricted IP (or do not expose in prod)

### Compose structure recommendation

Use `compose.yml` as the production stack source of truth (Redis/Celery services are already included).

Example deploy command pattern:

```bash
docker compose --env-file .env.production -f compose.yml up -d --build
```

## 5) DigitalOcean Provisioning Plan

## 5.1 Droplet baseline

- Ubuntu LTS (22.04 or 24.04)
- Size: at least 2 vCPU / 4 GB RAM for Web + API + DB + Redis + Celery on one host
- Attach project + tags in DigitalOcean for organization
- Enable DigitalOcean Backups at droplet level
- Add SSH key at droplet creation (no password auth workflow)

## 5.2 DNS and networking

- Point `A` records to droplet IP (`@` and optional `www`)
- Create DigitalOcean Cloud Firewall:
  - Inbound allow: `22/tcp` (restricted source IP if possible), `80/tcp`, `443/tcp`
  - Inbound deny: all else
  - Outbound allow: default

## 5.3 Host hardening checklist

- Create non-root sudo user
- Disable SSH password auth after key login verified
- Optionally disable direct root SSH login
- Install and configure UFW (`deny incoming`, `allow outgoing`, allow SSH/80/443)
- Install Fail2ban for SSH brute-force mitigation
- Keep OS patched (`apt update && apt upgrade` cadence)
- Enable unattended security updates

Reference baseline: DigitalOcean security best-practice guides and Ubuntu initial setup guides.

## 6) Environment Variables (required inventory)

This section is compiled from code (`apps/api`, `apps/web`), compose files, and docs.

## 6.1 Core infra and routing

| Variable | Required | Used by | Purpose |
|---|---|---|---|
| `DOMAIN` | Yes | Caddy | TLS site host and routing in `caddy/Caddyfile` |
| `API_BASE_URL` | Recommended | Web server runtime | Server-side API base (`http://api:8000` in container network) |
| `NEXT_PUBLIC_API_BASE_URL` | Recommended | Web client/runtime | Browser API base; keep empty for same-origin `/api/*` through Caddy |
| `NEXT_PUBLIC_SITE_URL` | Yes | Web SEO | Canonicals, sitemap, robots, JSON-LD origin |

## 6.2 Database

| Variable | Required | Used by | Purpose |
|---|---|---|---|
| `POSTGRES_DB` | Yes (or default) | DB/API/Celery | Database name |
| `POSTGRES_USER` | Yes (or default) | DB/API migrations | Superuser name |
| `POSTGRES_PASSWORD` | Yes | DB/API migrations | Superuser password |
| `POSTGRES_APP_USER` | Yes (or default) | DB/API/Celery | Least-privilege app user |
| `POSTGRES_APP_PASSWORD` | Yes | DB/API/Celery | App user password |
| `DATABASE_URL` | Yes | API + Celery | Primary app DB connection |
| `DATABASE_URL_ADMIN` | Yes for migrations | Alembic/API tasks | Migration/admin DB connection |

Notes:

- In compose, `DATABASE_URL` and `DATABASE_URL_ADMIN` are built from Postgres env vars.
- Ensure these are also available to Celery worker/beat containers.

## 6.3 API auth and security

| Variable | Required | Used by | Purpose |
|---|---|---|---|
| `JWT_SECRET` | Yes | API auth | Required secret for signing/verifying access tokens |
| `JWT_ALGORITHM` | Optional | API auth | Default `HS256` |
| `JWT_EXPIRES_MINUTES` | Optional | API auth | Token expiry window |
| `COOKIE_SECURE` | Yes in prod | API auth | Must be `true` for HTTPS cookies |
| `COOKIE_SAMESITE` | Optional | API auth | `lax` recommended for same-origin setup |
| `ENV` | Optional | API auth fallback | Impacts cookie secure fallback logic |
| `CORS_ORIGINS` | Optional | API app | Extra comma-separated allowed origins |

## 6.4 Celery and Redis

| Variable | Required | Used by | Purpose |
|---|---|---|---|
| `REDIS_URL` | Yes (for jobs parity) | API/Celery | Broker and result backend |
| `WEATHER_REFRESH_JITTER_MAX_SECONDS` | Optional | Celery tasks | Thundering-herd mitigation for weather refresh |

## 6.5 Logging

| Variable | Required | Used by | Purpose |
|---|---|---|---|
| `LOG_LEVEL` | Optional | API | Log verbosity |
| `LOG_FORMAT` | Recommended in prod | API | `json` in production |
| `LOG_ENV` | Recommended in prod | API | Set `production` |

## 6.6 Weather tuning

| Variable | Required | Used by | Purpose |
|---|---|---|---|
| `WEATHER_LOCATION_KEY` | Optional | API weather | Logical location identifier |
| `WEATHER_LATITUDE` | Optional | API weather | Forecast latitude |
| `WEATHER_LONGITUDE` | Optional | API weather | Forecast longitude |
| `WEATHER_CACHE_TTL_HOURS` | Optional | API weather | Cache freshness window |
| `WEATHER_DAILY_FETCH_CAP` | Optional | API weather | Provider call guardrail |
| `WEATHER_RETENTION_DAYS` | Optional | API weather | Snapshot retention |
| `WEATHER_FETCH_COUNTER_RETENTION_DAYS` | Optional | API weather | Counter retention |

## 6.7 Analytics (web)

| Variable | Required | Used by | Purpose |
|---|---|---|---|
| `NEXT_PUBLIC_UMAMI_WEBSITE_ID` | Optional but recommended | Web analytics | Enables Umami capture |
| `NEXT_PUBLIC_UMAMI_SCRIPT_URL` | Optional | Web analytics | Defaults to `https://cloud.umami.is/script.js` |
| `NEXT_PUBLIC_ANALYTICS_DEBUG` | Optional | Web analytics | Debug logging toggle |

## 7) Production `.env.production` Template

Keep this file on the server only (never commit secrets).

```bash
# Domain / routing
DOMAIN=srqhappenings.com
API_BASE_URL=http://api:8000
NEXT_PUBLIC_API_BASE_URL=
NEXT_PUBLIC_SITE_URL=https://srqhappenings.com

# Database
POSTGRES_DB=srq_hpn
POSTGRES_USER=srq_hpn
POSTGRES_PASSWORD=<strong-random>
POSTGRES_APP_USER=srq_hpn_app
POSTGRES_APP_PASSWORD=<strong-random>

# API auth
JWT_SECRET=<strong-random>
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=60
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
ENV=production

# API runtime
CORS_ORIGINS=https://srqhappenings.com,https://www.srqhappenings.com
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_ENV=production

# Celery/Redis
REDIS_URL=redis://redis:6379/0
WEATHER_REFRESH_JITTER_MAX_SECONDS=180

# Analytics
NEXT_PUBLIC_UMAMI_WEBSITE_ID=<umami-website-id>
NEXT_PUBLIC_UMAMI_SCRIPT_URL=https://cloud.umami.is/script.js
NEXT_PUBLIC_ANALYTICS_DEBUG=false
```

## 8) Build and Deploy Runbook

## 8.1 First-time bootstrap

```bash
# 1) Clone
sudo mkdir -p /opt/srq-hpn
sudo chown -R $USER:$USER /opt/srq-hpn
git clone <repo-url> /opt/srq-hpn
cd /opt/srq-hpn

# 2) Add secrets file
nano .env.production

# 3) Start DB first
docker compose --env-file .env.production up -d db

# 4) Start API (build) and run migrations
docker compose --env-file .env.production up -d --build api
docker compose --env-file .env.production exec api alembic upgrade head

# 5) Start full stack (includes Redis/Celery services)
docker compose --env-file .env.production -f compose.yml up -d --build
```

## 8.2 Deploy updates

```bash
cd /opt/srq-hpn
git pull origin main
docker compose --env-file .env.production -f compose.yml build
docker compose --env-file .env.production -f compose.yml run --rm api alembic upgrade head
docker compose --env-file .env.production -f compose.yml up -d
```

## 8.3 Post-deploy verification

```bash
docker ps
curl -I https://srqhappenings.com
curl https://srqhappenings.com/api/health
curl https://srqhappenings.com/api/db-health
curl https://srqhappenings.com/robots.txt
curl https://srqhappenings.com/sitemap.xml
```

Job verification:

```bash
docker compose --env-file .env.production logs -f celery-worker celery-beat
docker compose --env-file .env.production exec redis redis-cli ping
docker compose --env-file .env.production exec celery-worker celery -A app.celery_app call app.tasks.health_check
```

## 9) Backup, Restore, and Rollback

## 9.1 Database backup

```bash
docker exec srq-hpn-db pg_dump -U srq_hpn srq_hpn > /opt/backups/srq_hpn_$(date +%Y%m%d_%H%M%S).sql
```

Automate daily backups with retention and off-host copy (Spaces or other object storage).

## 9.2 Restore drill

```bash
cat /opt/backups/<backup-file>.sql | docker exec -i srq-hpn-db psql -U srq_hpn srq_hpn
```

Run quarterly restore tests.

## 9.3 App rollback

- Keep last known-good image tags available
- If deploy is bad:
  1) stop rollout, 2) restore previous image/tag, 3) restore DB only when schema/data incompatibility requires it

## 10) Security Controls Checklist

- [ ] DO Cloud Firewall configured (22/80/443 only)
- [ ] UFW configured and active
- [ ] SSH keys only; password auth disabled
- [ ] Non-root admin user for daily operations
- [ ] Fail2ban active for SSH
- [ ] Only Caddy ports exposed publicly; API/DB/Redis internal only
- [ ] Secrets stored outside git; `.env.production` file permissions restricted
- [ ] `COOKIE_SECURE=true` in production
- [ ] Logs reviewed and no secrets emitted
- [ ] Automated backups enabled and restore test scheduled

## 11) CI/CD Plan (follow-up to finish Step 5.2)

Create GitHub Actions workflows:

1. `ci.yml`
   - API lint/tests
   - Web lint/build

2. `deploy.yml` (manual + protected)
   - SSH to droplet
   - pull + build + migrate + compose up
   - health checks

Until CI/CD is in place, this document is the manual deploy runbook for v1.

## 12) Source Map

- `docs/roadmap.md` (Step 5 requirements)
- `docs/database-guide.md` (production setup, migration, backup/restore)
- `docs/celery-guide.md` (worker/beat/Redis operations)
- `docs/logging.md` (production logging settings)
- `docs/seo-implementation-checklist.md` (post-deploy SEO verification)
- `compose.yml` (current production stack)
- `compose.dev.yml` (reference for Redis/Celery services)
- `apps/api/app/core/auth.py` (JWT and cookie requirements)
- `apps/api/app/celery_app.py` and `apps/api/app/tasks.py` (job runtime requirements)
- `apps/web/src/lib/api.ts`, `apps/web/src/lib/seo.ts`, `apps/web/src/lib/analytics.ts`, `apps/web/src/app/providers/umami-provider.tsx` (web env requirements)
