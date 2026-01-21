"""make events.venue_id nullable + add uniqueness

Revision ID: cd8a08a488bf
Revises: 41591b70c2c5
Create Date: 2026-01-20 01:10:33.112986

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cd8a08a488bf"
down_revision: str | Sequence[str] | None = "41591b70c2c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1) events.venue_id should be nullable now (venue is on occurrences)
    op.alter_column("events", "venue_id", existing_type=sa.Integer(), nullable=True)

    # 2) unique constraint: events(source_id, external_id)
    op.create_unique_constraint(
        "uq_events_source_external_id",
        "events",
        ["source_id", "external_id"],
    )

    # 3) unique constraint: event_occurrences(event_id, start_datetime_utc)
    op.create_unique_constraint(
        "uq_event_occurrences_event_start",
        "event_occurrences",
        ["event_id", "start_datetime_utc"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_event_occurrences_event_start", "event_occurrences", type_="unique"
    )
    op.drop_constraint("uq_events_source_external_id", "events", type_="unique")

    op.alter_column("events", "venue_id", existing_type=sa.Integer(), nullable=False)
