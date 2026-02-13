"""add slot and indexes to weather reports

Revision ID: e4f9b7c2d1a0
Revises: c1d2e3f4a5b6
Create Date: 2026-02-13 14:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e4f9b7c2d1a0"
down_revision: str | Sequence[str] | None = "c1d2e3f4a5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "weather_reports",
        sa.Column("slot", sa.String(length=32), nullable=True),
    )

    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY provider, location_key, fetched_at
                    ORDER BY id
                ) AS rn
            FROM weather_reports
        )
        UPDATE weather_reports wr
        SET slot = CASE
            WHEN ranked.rn = 1 THEN 'today'
            WHEN ranked.rn = 2 THEN 'tomorrow'
            ELSE 'weekend'
        END
        FROM ranked
        WHERE wr.id = ranked.id
        """
    )

    op.alter_column("weather_reports", "slot", nullable=False)

    op.drop_index(
        "ix_weather_reports_provider_location_date_exp", table_name="weather_reports"
    )
    op.create_index(
        "ix_weather_reports_provider_location_exp_fetch",
        "weather_reports",
        ["provider", "location_key", "expires_at", "fetched_at"],
    )
    op.create_index(
        "ix_weather_reports_provider_location_slot_exp_fetch",
        "weather_reports",
        ["provider", "location_key", "slot", "expires_at", "fetched_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_weather_reports_provider_location_slot_exp_fetch",
        table_name="weather_reports",
    )
    op.drop_index(
        "ix_weather_reports_provider_location_exp_fetch", table_name="weather_reports"
    )
    op.create_index(
        "ix_weather_reports_provider_location_date_exp",
        "weather_reports",
        ["provider", "location_key", "forecast_date", "expires_at"],
    )

    op.drop_column("weather_reports", "slot")
