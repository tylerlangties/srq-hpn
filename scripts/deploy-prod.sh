#!/usr/bin/env bash

set -euo pipefail

ENV_FILE="${1:-.env.production}"
BRANCH="${2:-main}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

if ! command -v docker > /dev/null 2>&1; then
  echo "docker is required" >&2
  exit 1
fi

if ! command -v git > /dev/null 2>&1; then
  echo "git is required" >&2
  exit 1
fi

COMPOSE=(docker compose --env-file "$ENV_FILE" -f compose.yml)

retry() {
  local attempts="$1"
  local delay_seconds="$2"
  shift 2
  local count=1
  until "$@"; do
    if [[ "$count" -ge "$attempts" ]]; then
      return 1
    fi
    count=$((count + 1))
    sleep "$delay_seconds"
  done
}

echo "Updating repository on branch: $BRANCH"
git fetch origin
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "Validating compose configuration"
"${COMPOSE[@]}" config > /dev/null

echo "Building images"
"${COMPOSE[@]}" build

echo "Starting dependencies"
"${COMPOSE[@]}" up -d db redis

echo "Waiting for PostgreSQL"
retry 30 2 "${COMPOSE[@]}" exec -T db pg_isready -U "${POSTGRES_USER:-srq_hpn}" -d "${POSTGRES_DB:-srq_hpn}" > /dev/null

echo "Waiting for Redis"
retry 30 2 "${COMPOSE[@]}" exec -T redis redis-cli ping > /dev/null

echo "Running database migrations"
"${COMPOSE[@]}" run --rm api alembic upgrade head

echo "Starting application stack"
"${COMPOSE[@]}" up -d

echo "Running post-deploy health checks"
bash scripts/check-prod-health.sh "$ENV_FILE"

echo "Deploy completed successfully"
