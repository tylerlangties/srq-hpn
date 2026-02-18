"""purge big top events and add unique constraint on (source_id, external_id)

1. Resolve the Big Top source dynamically and delete its events/source_feeds.
   ON DELETE CASCADE on event_occurrences and event_categories handles
   child rows automatically.
2. Deduplicate any remaining events across ALL sources so the new
   constraint can be applied cleanly (keeps the lowest-id row per group).
3. Add a partial unique index on (source_id, external_id) WHERE
   external_id IS NOT NULL to prevent duplicate events at the DB level.

After running this migration, re-run the Big Top collector and ingestion
to re-populate events with proper categories and deduplication.

Revision ID: b5d7e9f1a3c6
Revises: a1b2c3d4e5f6
Create Date: 2026-02-09 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b5d7e9f1a3c6"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _resolve_bigtop_source_id(conn) -> int | None:
    rows = conn.execute(
        sa.text(
            """
            SELECT id, name, url
            FROM sources
            WHERE lower(name) LIKE :name_pattern
               OR lower(url) LIKE :url_pattern
            ORDER BY id
            """
        ),
        {
            "name_pattern": "%big top brewing%",
            "url_pattern": "%bigtopbrewing.com%",
        },
    ).all()

    if len(rows) == 0:
        return None

    if len(rows) > 1:
        matches = [f"id={row.id} name={row.name!r} url={row.url!r}" for row in rows]
        raise RuntimeError(
            f"Expected at most one Big Top source row, found {len(rows)}: {matches}"
        )

    return int(rows[0].id)


def upgrade() -> None:
    conn = op.get_bind()
    bigtop_source_id = _resolve_bigtop_source_id(conn)

    # ── 1. Purge all Big Top events and source feeds ────────────────────
    # CASCADE on event_occurrences and event_categories FKs handles
    # child rows automatically, so a single DELETE is sufficient.
    if bigtop_source_id is not None:
        result = conn.execute(
            sa.text("DELETE FROM events WHERE source_id = :sid"),
            {"sid": bigtop_source_id},
        )
        print(
            f"  Deleted {result.rowcount} Big Top events (source_id={bigtop_source_id})"
        )

        # Also clear stale source_feeds so the collector re-discovers only
        # current events from the GraphQL API on the next run.
        result = conn.execute(
            sa.text("DELETE FROM source_feeds WHERE source_id = :sid"),
            {"sid": bigtop_source_id},
        )
        print(f"  Deleted {result.rowcount} Big Top source feeds")
    else:
        print("  No Big Top source found; skipping Big Top purge step")

    # ── 2. Deduplicate remaining events across all sources ───────────────
    # For any (source_id, external_id) group with more than one row,
    # keep the row with the lowest id and delete the rest.
    # This ensures the UNIQUE index can be created without conflict.
    result = conn.execute(
        sa.text("""
            DELETE FROM events
            WHERE id IN (
                SELECT e.id
                FROM events e
                JOIN (
                    SELECT source_id, external_id, MIN(id) AS keep_id
                    FROM events
                    WHERE external_id IS NOT NULL
                    GROUP BY source_id, external_id
                    HAVING COUNT(*) > 1
                ) dups
                ON  e.source_id   = dups.source_id
                AND e.external_id = dups.external_id
                AND e.id          != dups.keep_id
            )
        """)
    )
    if result.rowcount:
        print(f"  Deduplicated {result.rowcount} duplicate events across other sources")

    # ── 3. Add partial unique index ──────────────────────────────────────
    # Partial index (WHERE external_id IS NOT NULL) avoids NULL-equality
    # issues and matches the application-level dedup semantics.
    # Use IF NOT EXISTS in case the index was already created by
    # SQLAlchemy metadata.create_all() from the updated model.
    conn.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_events_source_external_id "
            "ON events (source_id, external_id) "
            "WHERE external_id IS NOT NULL"
        )
    )


def downgrade() -> None:
    op.drop_index("uq_events_source_external_id", table_name="events")
    # Deleted event data cannot be restored; only the index is reversible.
