"""add source_items table

Revision ID: cc6d6e53220b
Revises: cd8a08a488bf
Create Date: 2026-01-21 00:28:27.201607

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cc6d6e53220b"
down_revision: str | Sequence[str] | None = "cd8a08a488bf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Stable identifier for this iCal file/feed within the source.
        # Used for deduplication: unique(source_id, external_id)
        # Examples: "mustdo:event-slug", "2025-01" (for monthly feeds), or URL hash
        # NOTE: This is NOT the same as Event.external_id (which is the iCal event UID)
        sa.Column("external_id", sa.String(length=255), nullable=False),
        # Human-facing page URL (preferred for users)
        sa.Column("page_url", sa.Text(), nullable=True),
        # The per-event iCal URL fetched
        sa.Column("ical_url", sa.Text(), nullable=False),
        # Basic lifecycle tracking
        sa.Column("status", sa.String(length=32), nullable=False, server_default="new"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        # HTTP caching / debug
        sa.Column("etag", sa.String(length=255), nullable=True),
        sa.Column("last_modified", sa.String(length=255), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Uniqueness: a source can only have one item with a given external_id
    op.create_unique_constraint(
        "uq_source_items_source_external_id",
        "source_items",
        ["source_id", "external_id"],
    )

    # Helpful indexes
    op.create_index("ix_source_items_source_id", "source_items", ["source_id"])
    op.create_index("ix_source_items_status", "source_items", ["status"])
    op.create_index("ix_source_items_last_seen_at", "source_items", ["last_seen_at"])


def downgrade() -> None:
    op.drop_index("ix_source_items_last_seen_at", table_name="source_items")
    op.drop_index("ix_source_items_status", table_name="source_items")
    op.drop_index("ix_source_items_source_id", table_name="source_items")
    op.drop_constraint(
        "uq_source_items_source_external_id", "source_items", type_="unique"
    )
    op.drop_table("source_items")
