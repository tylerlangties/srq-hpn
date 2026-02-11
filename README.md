# SRQ Happenings (`srq-hpn`)

A local events platform for **Sarasota, FL**, focused on aggregating, organizing, and presenting events in a clean, user-friendly way.

This repository is a **monorepo** containing:
- a **Next.js + React + TypeScript** frontend
- a **FastAPI + Python** backend
- a **PostgreSQL** database (via Docker)
- **Celery** for background tasks (event ingestion, scrapers)
- shared tooling for linting, formatting, and development

---

## 🧱 Tech Stack

### Frontend
- **Next.js 16** (React 19 + TypeScript)
- Tailwind CSS v4
- Decap CMS (headless CMS for articles)
- Runs on `http://localhost:3000`

### Backend
- **FastAPI**
- **SQLAlchemy 2.0** (ORM)
- **Alembic** (database migrations)
- **Celery** (background tasks)
- **Redis** (message broker for Celery)
- **PostgreSQL 16**
- Runs on `http://localhost:8000`

### Infrastructure
- **Caddy** (reverse proxy, automatic HTTPS in production)
- **Docker Compose** (database, full dev stack, production)
- **Flower** (Celery monitoring at `http://localhost:5555` in dev)

### Tooling
- **pnpm** (monorepo package manager)
- **Ruff** (Python linting & formatting)
- **pre-commit** (git hooks)

---

## 📁 Repository Structure

```text
srq-hpn/
├── apps/
│   ├── web/            # Next.js frontend
│   └── api/            # FastAPI backend
├── caddy/              # Caddy reverse proxy config (production)
├── db/                 # PostgreSQL init scripts
├── docs/               # Documentation (database, Celery, etc.)
├── compose.yml         # Production stack (Caddy, Web, API, DB)
├── compose.dev.yml     # Development stack (+ Redis, Celery, Flower)
├── compose.db.yml      # Database only (for local dev without Docker)
├── pnpm-workspace.yaml
├── package.json        # Root scripts
└── README.md
```

---

## 🚀 Quick Start

### Option A: Full Docker (recommended)

Requires `.env.local` with database credentials. See `docs/database-guide.md` for details.

```bash
pnpm docker:dev
```

This starts: DB, Redis, API, Celery worker, Celery beat, Flower, and Web.

- **Web**: http://localhost:3000
- **API**: http://localhost:8000
- **Flower** (Celery): http://localhost:5555

### API Routing and Namespaces

The app uses a reverse proxy (Caddy) in Docker environments. Route ownership is:

- **FastAPI public API**: `/api/*` (for example `/api/events/range`)
- **Next.js route handlers**: `/content-api/*` (for example `/content-api/articles`)

Why this split exists:

- Both Next.js and FastAPI can define `/api/*` routes.
- Reserving `/api/*` for FastAPI avoids conflicts and keeps backend endpoints conventional.
- Internal Next.js handlers use `/content-api/*` to stay explicit and collision-free.

In Docker dev:

- Open the app at `http://localhost:3000` (served through Caddy).
- Browser calls to `/api/*` are proxied to FastAPI.
- Browser calls to `/content-api/*` are handled by Next.js.
- `http://localhost:8000` is still exposed for direct API debugging.

### Option B: Local (DB + API + Web separately)

```bash
# 1. Start database
pnpm db:up

# 2. Create API venv and run migrations (see apps/api/)
pnpm dev:api

# 3. In another terminal: frontend
pnpm dev:web
```

---

## 📜 Scripts

| Command | Description |
|---------|-------------|
| `pnpm dev:web` | Start Next.js dev server |
| `pnpm dev:cms` | Start Next.js + Decap CMS |
| `pnpm dev:api` | Start FastAPI with uvicorn |
| `pnpm lint:web` | Lint frontend |
| `pnpm lint:api` | Lint API (Ruff) |
| `pnpm format:api` | Format API (Ruff) |
| `pnpm db:up` | Start Postgres (compose.db.yml) |
| `pnpm db:down` | Stop Postgres |
| `pnpm docker:dev` | Start full dev stack |
| `pnpm docker:dev:build` | Build and start dev stack |
| `pnpm docker:dev:down` | Stop dev stack |
| `pnpm docker:migrate` | Run migrations (dev container) |

---

## 📚 Documentation

- [Database & Infrastructure](docs/database-guide.md)
- [Celery Guide](docs/celery-guide.md)
- [Logging](docs/logging.md)
- [Roadmap](docs/roadmap.md)
