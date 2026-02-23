from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "5e2d9a7b1c3f"
down_revision: str | Sequence[str] | None = "b7a1d3e9c4f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("venues", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("venues", "description")
