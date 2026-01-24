"""add source_fetch_runs table

Revision ID: 1591fe31fd56
Revises: cc6d6e53220b
Create Date: 2026-01-23 00:39:47.925452

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1591fe31fd56"
down_revision: str | Sequence[str] | None = "cc6d6e53220b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_fetch_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fetch_url", sa.Text(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="running"
        ),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.Text(), nullable=True),
        sa.Column("bytes", sa.Integer(), nullable=True),
        sa.Column("etag", sa.Text(), nullable=True),
        sa.Column("last_modified", sa.Text(), nullable=True),
        sa.Column("events_parsed", sa.Integer(), nullable=True),
        sa.Column("events_ingested", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
    )

    op.create_index(
        "ix_source_fetch_runs_source_id", "source_fetch_runs", ["source_id"]
    )
    op.create_index(
        "ix_source_fetch_runs_started_at", "source_fetch_runs", ["started_at"]
    )
    op.create_index("ix_source_fetch_runs_status", "source_fetch_runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_source_fetch_runs_status", table_name="source_fetch_runs")
    op.drop_index("ix_source_fetch_runs_started_at", table_name="source_fetch_runs")
    op.drop_index("ix_source_fetch_runs_source_id", table_name="source_fetch_runs")
    op.drop_table("source_fetch_runs")
