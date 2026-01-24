"""add events_parsed and events_ingested to source_items

Revision ID: 89516b7d3ee9
Revises: 1591fe31fd56
Create Date: 2026-01-23 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "89516b7d3ee9"
down_revision: str | Sequence[str] | None = "1591fe31fd56"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add events tracking fields to source_items (will be renamed to source_feeds in next migration)
    op.add_column(
        "source_items",
        sa.Column("events_parsed", sa.Integer(), nullable=True),
    )
    op.add_column(
        "source_items",
        sa.Column("events_ingested", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("source_items", "events_ingested")
    op.drop_column("source_items", "events_parsed")
