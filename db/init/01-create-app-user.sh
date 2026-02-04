#!/bin/bash
# This script runs automatically when PostgreSQL initializes for the first time.
# It creates a limited app user that can only read/write data (not modify schema).

set -e

echo "Creating limited app user: $POSTGRES_APP_USER"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create the limited app user
    CREATE USER $POSTGRES_APP_USER WITH PASSWORD '$POSTGRES_APP_PASSWORD';
    
    -- Allow connecting to the database
    GRANT CONNECT ON DATABASE $POSTGRES_DB TO $POSTGRES_APP_USER;
    
    -- Allow using the public schema
    GRANT USAGE ON SCHEMA public TO $POSTGRES_APP_USER;
    
    -- Allow read/write on all FUTURE tables (created by migrations)
    ALTER DEFAULT PRIVILEGES FOR USER $POSTGRES_USER IN SCHEMA public
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO $POSTGRES_APP_USER;
    
    -- Allow using sequences (needed for auto-increment IDs)
    ALTER DEFAULT PRIVILEGES FOR USER $POSTGRES_USER IN SCHEMA public
        GRANT USAGE, SELECT ON SEQUENCES TO $POSTGRES_APP_USER;
EOSQL

echo "Limited app user '$POSTGRES_APP_USER' created successfully"
