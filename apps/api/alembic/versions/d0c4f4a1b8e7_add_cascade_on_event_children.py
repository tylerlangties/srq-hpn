"""add cascade on event children

Revision ID: d0c4f4a1b8e7
Revises: 6f2b9d8c8c12
Create Date: 2026-01-31 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d0c4f4a1b8e7"
down_revision: str | Sequence[str] | None = "6f2b9d8c8c12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("event_occurrences") as batch_op:
        batch_op.drop_constraint("event_occurrences_event_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "event_occurrences_event_id_fkey",
            "events",
            ["event_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("event_categories") as batch_op:
        batch_op.drop_constraint("event_categories_event_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "event_categories_event_id_fkey",
            "events",
            ["event_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("event_categories") as batch_op:
        batch_op.drop_constraint("event_categories_event_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "event_categories_event_id_fkey",
            "events",
            ["event_id"],
            ["id"],
        )

    with op.batch_alter_table("event_occurrences") as batch_op:
        batch_op.drop_constraint("event_occurrences_event_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "event_occurrences_event_id_fkey",
            "events",
            ["event_id"],
            ["id"],
        )
