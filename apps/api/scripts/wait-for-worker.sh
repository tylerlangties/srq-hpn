#!/bin/sh
# Wait for Celery worker to be ready before starting a command
#
# This script polls the Celery worker via the inspect ping command.
# Once a worker responds, it executes the command passed as arguments.
#
# Usage: ./wait-for-worker.sh <command to run after worker is ready>
# Example: ./wait-for-worker.sh celery -A app.celery_app flower --port=5555

set -e

MAX_RETRIES=30      # Maximum number of attempts (30 * 2s = 60s max wait)
RETRY_INTERVAL=2    # Seconds between retries

echo "Waiting for Celery worker to be ready..."

retries=0
while [ $retries -lt $MAX_RETRIES ]; do
    # Try to ping the worker
    # The ping command returns a response if any worker is available
    if celery -A app.celery_app inspect ping --timeout=2 > /dev/null 2>&1; then
        echo "Worker is ready!"
        echo "Starting: $@"
        exec "$@"
    fi

    retries=$((retries + 1))
    echo "Worker not ready yet (attempt $retries/$MAX_RETRIES). Retrying in ${RETRY_INTERVAL}s..."
    sleep $RETRY_INTERVAL
done

echo "ERROR: Worker did not become ready after $MAX_RETRIES attempts"
exit 1
