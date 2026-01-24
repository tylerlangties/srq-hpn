"""rename source_items to source_feeds

Revision ID: 35bca58fef34
Revises: 89516b7d3ee9
Create Date: 2026-01-23 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "35bca58fef34"
down_revision: str | Sequence[str] | None = "89516b7d3ee9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Rename table
    op.rename_table("source_items", "source_feeds")

    # Rename unique constraint
    op.drop_constraint(
        "uq_source_items_source_external_id", "source_feeds", type_="unique"
    )
    op.create_unique_constraint(
        "uq_source_feeds_source_external_id",
        "source_feeds",
        ["source_id", "external_id"],
    )

    # Rename indexes
    op.drop_index("ix_source_items_source_id", table_name="source_feeds")
    op.drop_index("ix_source_items_status", table_name="source_feeds")
    op.drop_index("ix_source_items_last_seen_at", table_name="source_feeds")

    op.create_index("ix_source_feeds_source_id", "source_feeds", ["source_id"])
    op.create_index("ix_source_feeds_status", "source_feeds", ["status"])
    op.create_index("ix_source_feeds_last_seen_at", "source_feeds", ["last_seen_at"])


def downgrade() -> None:
    # Rename indexes back
    op.drop_index("ix_source_feeds_last_seen_at", table_name="source_feeds")
    op.drop_index("ix_source_feeds_status", table_name="source_feeds")
    op.drop_index("ix_source_feeds_source_id", table_name="source_feeds")

    op.create_index("ix_source_items_source_id", "source_feeds", ["source_id"])
    op.create_index("ix_source_items_status", "source_feeds", ["status"])
    op.create_index("ix_source_items_last_seen_at", "source_feeds", ["last_seen_at"])

    # Rename unique constraint back
    op.drop_constraint(
        "uq_source_feeds_source_external_id", "source_feeds", type_="unique"
    )
    op.create_unique_constraint(
        "uq_source_items_source_external_id",
        "source_feeds",
        ["source_id", "external_id"],
    )

    # Rename table back
    op.rename_table("source_feeds", "source_items")
