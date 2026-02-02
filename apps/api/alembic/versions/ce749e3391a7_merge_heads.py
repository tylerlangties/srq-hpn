"""merge heads

Revision ID: ce749e3391a7
Revises: b4c6d8e0f3a1, d0c4f4a1b8e7
Create Date: 2026-01-31 02:20:08.305359

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "ce749e3391a7"
down_revision: str | Sequence[str] | None = ("b4c6d8e0f3a1", "d0c4f4a1b8e7")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
