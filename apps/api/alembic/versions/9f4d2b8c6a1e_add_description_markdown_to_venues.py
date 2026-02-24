from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "9f4d2b8c6a1e"
down_revision: str | Sequence[str] | None = "7c1a9e5d2b4f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("venues", sa.Column("description_markdown", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("venues", "description_markdown")
