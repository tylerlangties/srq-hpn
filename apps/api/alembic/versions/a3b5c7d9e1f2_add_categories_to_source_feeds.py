"""add categories to source_feeds

Revision ID: a3b5c7d9e1f2
Revises: 6f2b9d8c8c12
Create Date: 2026-01-27 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3b5c7d9e1f2"
down_revision: str | Sequence[str] | None = "6f2b9d8c8c12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add categories column to store custom category names (comma-separated)
    # These categories are applied to events during ingestion
    op.add_column(
        "source_feeds",
        sa.Column("categories", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("source_feeds", "categories")
