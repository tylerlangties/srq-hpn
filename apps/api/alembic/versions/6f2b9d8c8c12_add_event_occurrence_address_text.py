"""add address_text to event_occurrences

Revision ID: 6f2b9d8c8c12
Revises: 35bca58fef34
Create Date: 2026-01-26 12:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6f2b9d8c8c12"
down_revision: str | Sequence[str] | None = "35bca58fef34"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "event_occurrences", sa.Column("address_text", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("event_occurrences", "address_text")
