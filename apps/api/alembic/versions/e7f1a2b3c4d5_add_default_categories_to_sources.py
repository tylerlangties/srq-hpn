"""add default_categories to sources

Revision ID: e7f1a2b3c4d5
Revises: ce749e3391a7
Create Date: 2026-02-07 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e7f1a2b3c4d5"
down_revision: str | Sequence[str] | None = "ce749e3391a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Blanket categories applied to every event ingested from this source.
    # Stored as a comma-separated string (e.g. "Performing Arts,Live Music").
    op.add_column(
        "sources",
        sa.Column("default_categories", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sources", "default_categories")
