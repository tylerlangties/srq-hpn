from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "7c1a9e5d2b4f"
down_revision: str | Sequence[str] | None = "5e2d9a7b1c3f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("venues", sa.Column("hero_image_path", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("venues", "hero_image_path")
