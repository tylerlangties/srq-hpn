"""add event hidden

Revision ID: b4c6d8e0f3a1
Revises: a3b5c7d9e1f2
Create Date: 2026-01-27 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4c6d8e0f3a1"
down_revision: str | Sequence[str] | None = "a3b5c7d9e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("events", "hidden")
