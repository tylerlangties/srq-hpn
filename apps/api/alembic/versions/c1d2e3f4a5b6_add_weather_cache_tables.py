"""add weather cache tables

Revision ID: c1d2e3f4a5b6
Revises: 9c2e7b4a1d10
Create Date: 2026-02-13 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: str | Sequence[str] | None = "9c2e7b4a1d10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "weather_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("location_key", sa.String(length=128), nullable=False),
        sa.Column("forecast_date", sa.Date(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_weather_reports_provider_location_date_exp",
        "weather_reports",
        ["provider", "location_key", "forecast_date", "expires_at"],
    )
    op.create_index("ix_weather_reports_fetched_at", "weather_reports", ["fetched_at"])

    op.create_table(
        "weather_fetch_counters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("fetch_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_fetch_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "provider",
            "day",
            name="uq_weather_fetch_counters_provider_day",
        ),
    )


def downgrade() -> None:
    op.drop_table("weather_fetch_counters")
    op.drop_index("ix_weather_reports_fetched_at", table_name="weather_reports")
    op.drop_index(
        "ix_weather_reports_provider_location_date_exp", table_name="weather_reports"
    )
    op.drop_table("weather_reports")
