#!/usr/bin/env bash

set -euo pipefail

ENV_FILE="${1:-.env.production}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

DOMAIN_VALUE="${DOMAIN:-}"
if [[ -z "$DOMAIN_VALUE" ]]; then
  echo "DOMAIN is not set in $ENV_FILE" >&2
  exit 1
fi

BASE_URL="https://${DOMAIN_VALUE}"
if [[ -n "${HEALTH_BASE_URL:-}" ]]; then
  BASE_URL="$HEALTH_BASE_URL"
fi

curl -fsS "${BASE_URL}/api/health" > /dev/null
curl -fsS "${BASE_URL}/api/db-health" > /dev/null
curl -fsS "${BASE_URL}/robots.txt" > /dev/null
curl -fsS "${BASE_URL}/sitemap.xml" > /dev/null

echo "Health checks passed for ${BASE_URL}"
