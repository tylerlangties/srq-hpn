# Infrastructure & Database Guide

This guide covers infrastructure setup, database management, and production deployments.

## Architecture Overview

### Production Stack

```
Internet → Caddy (HTTPS/reverse proxy) → Web (Next.js) / API (FastAPI) → Database (PostgreSQL)
```

| Component | Purpose |
|-----------|---------|
| **Caddy** | Reverse proxy, automatic HTTPS via Let's Encrypt |
| **Web** | Next.js frontend (port 3000, internal only) |
| **API** | FastAPI backend (port 8000, internal only) |
| **Database** | PostgreSQL 16 (port 5432, internal only) |

### Database Users

The application uses two database users for security:

| User | Purpose | Permissions |
|------|---------|-------------|
| `srq_hpn` | Superuser for migrations and admin tools | Full access (CREATE, DROP, ALTER, etc.) |
| `srq_hpn_app` | Limited user for the running API | Read/write data only (SELECT, INSERT, UPDATE, DELETE) |

This separation ensures that even if the application is compromised, an attacker cannot modify the database schema or drop tables.

### URL Routing (Production)

Caddy routes requests based on path:

| Request | Routed To |
|---------|-----------|
| `https://yourdomain.com/api/*` | API container |
| `https://yourdomain.com/*` | Web container |

This means your frontend can call `/api/events` without specifying a full URL.

---

## Local Development

### Daily Commands

```bash
# Start all services (DB, API, Web)
pnpm docker:dev

# Stop all services
pnpm docker:dev:down

# Run migrations (after pulling new code)
pnpm docker:migrate

# View logs
pnpm docker:logs
pnpm docker:logs:api
pnpm docker:logs:web

# Rebuild containers (after Dockerfile changes)
pnpm docker:dev:build
```

### Connecting with Beekeeper/pgAdmin

| Setting | Value |
|---------|-------|
| Host | `localhost` |
| Port | `5432` |
| Database | `srq_hpn` |
| User | `srq_hpn` (superuser) |
| Password | Value from `.env.local` |

### Creating New Migrations

```bash
# Option 1: Inside the Docker container
docker exec -it srq-hpn-api-dev alembic revision --autogenerate -m "describe your change"

# Option 2: Native development (outside Docker)
cd apps/api && source .venv/bin/activate
alembic revision --autogenerate -m "describe your change"
```

After creating a migration, always:
1. Review the generated file in `apps/api/alembic/versions/`
2. Test it locally with `pnpm docker:migrate`
3. Commit the migration file to git

### Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| "Table doesn't exist" | Migrations not run | `pnpm docker:migrate` |
| "Connection refused" | Containers not running | `docker ps` to check, then `pnpm docker:dev` |
| "Permission denied" on table | New table not granted to app user | Re-run migration (auto-grants permissions) |
| Init script didn't run | Volume already existed | Delete volume and restart (see below) |

#### Nuclear Reset (when things are really broken)

```bash
pnpm docker:dev:down
docker volume rm srq-hpn_postgres_data_dev
pnpm docker:dev:build
pnpm docker:migrate
```

> **Warning:** This deletes all local data. Only use when necessary.

---

## Production Setup

### Prerequisites

- Docker and Docker Compose installed on your server
- Domain/IP address for your server
- Strong, unique passwords generated (see below)

### Step 1: Generate Secure Passwords

```bash
# Generate strong passwords (run locally, save output securely)
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)"
echo "POSTGRES_APP_PASSWORD=$(openssl rand -base64 32)"
```

### Step 2: Set Environment Variables

On your production server, set these environment variables. How you do this depends on your deployment platform:

**Option A: `.env` file on server** (simple deployments)
```bash
# /path/to/app/.env.production

# Your domain (required for Caddy HTTPS)
DOMAIN=yourdomain.com

# Database superuser (for migrations)
POSTGRES_DB=srq_hpn
POSTGRES_USER=srq_hpn
POSTGRES_PASSWORD=<generated-superuser-password>

# Database app user (for running API)
POSTGRES_APP_USER=srq_hpn_app
POSTGRES_APP_PASSWORD=<generated-app-password>

# Frontend API URL (empty = use relative URLs via Caddy)
NEXT_PUBLIC_API_BASE_URL=
```

**Option B: Secrets Manager** (recommended for cloud deployments)
- AWS: Use AWS Secrets Manager or Parameter Store
- GCP: Use Secret Manager
- Azure: Use Key Vault

Configure your deployment to inject these as environment variables.

> **Note:** `NEXT_PUBLIC_API_BASE_URL` can be left empty in production. Since Caddy routes `/api/*` to the API, the frontend can use relative URLs like `/api/events`.

### Step 3: Deploy and Initialize

```bash
# Clone your repository on the server
git clone <your-repo> /opt/srq-hpn
cd /opt/srq-hpn

# Start the database first (it needs to initialize)
docker compose --env-file .env.production up -d db

# Wait for it to be healthy (check logs)
docker logs -f srq-hpn-db
# Look for: "database system is ready to accept connections"
# And: "Limited app user 'srq_hpn_app' created successfully"
# Press Ctrl+C to exit logs

# Build and start the API (needed for migrations)
docker compose --env-file .env.production up -d --build api

# Run migrations
docker compose --env-file .env.production exec api alembic upgrade head

# Start all services (includes Caddy reverse proxy)
docker compose --env-file .env.production up -d
```

### Step 4: Verify Everything Works

```bash
# Check all containers are running (should see: caddy, db, api, web)
docker ps

# Test via Caddy (HTTPS) - this is how users will access it
curl -I https://yourdomain.com
# Should return: HTTP/2 200

curl https://yourdomain.com/api/health
# Should return: {"ok":true,"service":"api"}

curl https://yourdomain.com/api/db-health
# Should return: {"db_ok":true,"now":"..."}
```

### Step 5: DNS Configuration

Point your domain to your server's IP address:

| Type | Name | Value |
|------|------|-------|
| A | @ | Your server's IP |
| A | www | Your server's IP (optional) |

Caddy will automatically obtain and renew SSL certificates from Let's Encrypt once DNS is configured.

### Caddy Reverse Proxy (Included)

The production Docker Compose includes Caddy, which provides:

- **Automatic HTTPS** via Let's Encrypt (no manual certificate management)
- **Reverse proxy** routing (`/api/*` → API, `/*` → Web)
- **Security headers** (X-Frame-Options, X-Content-Type-Options, etc.)
- **HTTP → HTTPS redirect** automatic

**Caddy configuration file:** `caddy/Caddyfile`

```
{$DOMAIN} {
    handle /api/* {
        reverse_proxy api:8000
    }
    handle {
        reverse_proxy web:3000
    }
}
```

**To customize:** Edit `caddy/Caddyfile` and restart:
```bash
docker compose --env-file .env.production restart caddy
```

---

## Production Operations

### Deploying Updates

```bash
# 1. Pull latest code
cd /opt/srq-hpn
git pull origin main

# 2. Rebuild containers (only rebuilds changed images)
docker compose --env-file .env.production build

# 3. Run migrations (if any)
docker compose --env-file .env.production exec api alembic upgrade head

# 4. Restart services (zero-downtime for Caddy)
docker compose --env-file .env.production up -d
```

**If you changed `caddy/Caddyfile`:**
```bash
docker compose --env-file .env.production restart caddy
```

### Running Migrations in Production

```bash
# Always run migrations BEFORE restarting the app
docker compose --env-file .env.production run --rm api alembic upgrade head

# Or if containers are already running:
pnpm docker:migrate:prod
```

### Backing Up the Database

```bash
# Create a backup
docker exec srq-hpn-db pg_dump -U srq_hpn srq_hpn > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup (WARNING: destructive)
cat backup_file.sql | docker exec -i srq-hpn-db psql -U srq_hpn srq_hpn
```

For production, set up automated daily backups. If using a managed database (AWS RDS, etc.), enable automated backups in the console.

### Viewing Production Logs

```bash
# All services
docker compose --env-file .env.production logs -f

# Specific service
docker logs -f srq-hpn-caddy  # Reverse proxy / HTTPS
docker logs -f srq-hpn-api    # Backend API
docker logs -f srq-hpn-web    # Frontend
docker logs -f srq-hpn-db     # Database
```

### Connecting to Production Database

**Do NOT expose port 5432 to the internet.** Instead:

1. SSH into your server
2. Connect locally:
   ```bash
   docker exec -it srq-hpn-db psql -U srq_hpn srq_hpn
   ```

Or use SSH tunneling for GUI tools:
```bash
# On your local machine
ssh -L 5433:localhost:5432 user@your-server

# Then connect Beekeeper to localhost:5433
```

---

## Production Checklist

### Before Going Live

**Security:**
- [ ] Generated strong, unique passwords (`openssl rand -base64 32`)
- [ ] Passwords stored in secrets manager (not in git)
- [ ] Database port (5432) NOT exposed to internet
- [ ] API/Web ports (8000, 3000) NOT exposed — only Caddy (80, 443)

**Domain & HTTPS:**
- [ ] Domain DNS pointing to server IP
- [ ] `DOMAIN` environment variable set correctly
- [ ] Caddy container running and healthy
- [ ] HTTPS working (check with `curl -I https://yourdomain.com`)
- [ ] HTTP redirects to HTTPS

**Database:**
- [ ] Tested migrations locally before deploying
- [ ] Database initialized with app user
- [ ] Set up automated backups
- [ ] Tested restoring from backup

**Monitoring:**
- [ ] Set up monitoring/alerts for container health
- [ ] Log aggregation configured (optional)

### Ongoing Maintenance

- [ ] Monitor disk space (databases and Caddy certificates)
- [ ] Review and rotate passwords periodically
- [ ] Keep Docker images updated for security patches
- [ ] Test backup restoration quarterly
- [ ] Check Caddy certificate renewal (automatic, but verify)

---

## Database Management Tips

### Safe Practices

**Always use transactions for manual changes:**
```sql
BEGIN;
-- your changes here
SELECT * FROM affected_table;  -- verify results
COMMIT;  -- or ROLLBACK; if something's wrong
```

**Before destructive operations:**
1. Create a backup
2. Test on local/staging first
3. Run during low-traffic periods
4. Have a rollback plan

### Things to Never Do in Production

- `DROP TABLE` without a backup
- `DELETE FROM table` without a `WHERE` clause
- Manually modify schema (always use migrations)
- Share superuser credentials with the application
- Run untested migrations

---

## Golden Rules

1. **Migrations are your source of truth** — never manually change the production schema
2. **Test locally first** — always run migrations on dev before production
3. **Backups before changes** — especially before running migrations
4. **Least privilege** — the app only gets read/write access, not schema modification
5. **No secrets in git** — use environment variables or secrets managers

---

## Quick Reference

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DOMAIN` | Your domain (e.g., `example.com`) | **Yes (production)** |
| `POSTGRES_DB` | Database name | No (default: `srq_hpn`) |
| `POSTGRES_USER` | Superuser name | No (default: `srq_hpn`) |
| `POSTGRES_PASSWORD` | Superuser password | **Yes (production)** |
| `POSTGRES_APP_USER` | Limited user name | No (default: `srq_hpn_app`) |
| `POSTGRES_APP_PASSWORD` | Limited user password | **Yes (production)** |
| `DATABASE_URL` | Connection string for app | Auto-generated in Docker |
| `DATABASE_URL_ADMIN` | Connection string for migrations | Auto-generated in Docker |
| `NEXT_PUBLIC_API_BASE_URL` | API URL for frontend | Empty in prod (uses relative URLs) |

### File Locations

| File | Purpose |
|------|---------|
| `compose.yml` | Production Docker Compose (includes Caddy) |
| `compose.dev.yml` | Development Docker Compose |
| `compose.db.yml` | Standalone database (for native dev) |
| `caddy/Caddyfile` | Reverse proxy configuration |
| `db/init/01-create-app-user.sh` | Creates limited user on DB init |
| `apps/api/alembic/` | Database migrations |
| `.env.local` | Local environment variables |

### Ports

| Port | Service | Exposed in Production |
|------|---------|----------------------|
| 80 | Caddy (HTTP → HTTPS redirect) | Yes |
| 443 | Caddy (HTTPS) | Yes |
| 3000 | Web (Next.js) | No (internal only) |
| 8000 | API (FastAPI) | No (internal only) |
| 5432 | Database (PostgreSQL) | No (internal only) |
