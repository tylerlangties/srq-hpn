"""occurrence location_text + venue_id + venue_aliases

Revision ID: 41591b70c2c5
Revises: 23d64303c67a
Create Date: 2026-01-19 00:52:10.261086

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "41591b70c2c5"
down_revision = "23d64303c67a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # event_occurrences: add location_text + venue_id
    op.add_column(
        "event_occurrences", sa.Column("location_text", sa.Text(), nullable=True)
    )
    op.add_column(
        "event_occurrences", sa.Column("venue_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_event_occurrences_venue_id",
        "event_occurrences",
        "venues",
        ["venue_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # venue_aliases table
    op.create_table(
        "venue_aliases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("venue_id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.Text(), nullable=False),
        sa.Column("alias_normalized", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["venue_id"], ["venues.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_venue_aliases_venue_id", "venue_aliases", ["venue_id"])
    op.create_index(
        "ux_venue_aliases_alias_normalized",
        "venue_aliases",
        ["alias_normalized"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_venue_aliases_alias_normalized", table_name="venue_aliases")
    op.drop_index("ix_venue_aliases_venue_id", table_name="venue_aliases")
    op.drop_table("venue_aliases")

    op.drop_constraint(
        "fk_event_occurrences_venue_id", "event_occurrences", type_="foreignkey"
    )
    op.drop_column("event_occurrences", "venue_id")
    op.drop_column("event_occurrences", "location_text")
