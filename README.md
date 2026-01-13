# SRQ Happenings (`srq-hpn`)

A local events platform for **Sarasota, FL**, focused on aggregating, organizing, and presenting events in a clean, user-friendly way.

This repository is a **monorepo** containing:
- a **Next.js + React + TypeScript** frontend
- a **FastAPI + Python** backend
- a **PostgreSQL** database (via Docker)
- shared tooling for linting, formatting, and development

---

## 🧱 Tech Stack

### Frontend
- **Next.js** (React + TypeScript)
- Tailwind CSS
- Runs on `http://localhost:3000`

### Backend
- **FastAPI**
- **SQLAlchemy 2.0** (ORM)
- **Alembic** (database migrations)
- **PostgreSQL**
- Runs on `http://localhost:8000`

### Tooling
- **pnpm** (monorepo package manager)
- **Docker Compose** (database)
- **Ruff** (Python linting & formatting)
- **pre-commit** (git hooks)

---

## 📁 Repository Structure

```text
srq-hpn/
├── apps/
│   ├── web/            # Next.js frontend
│   └── api/            # FastAPI backend
├── infra/              # Infrastructure (Docker, etc.)
├── compose.db.yml      # Postgres service
├── pnpm-workspace.yaml
├── package.json        # Root scripts
└── README.md

