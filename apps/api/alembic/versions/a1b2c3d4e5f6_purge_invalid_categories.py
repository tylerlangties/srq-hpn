"""purge invalid categories

Delete categories (and their event_categories links) that are not in the
canonical CATEGORY_KEYWORDS registry defined in app.services.categorize.

Revision ID: a1b2c3d4e5f6
Revises: f8a2b4c6d8e0
Create Date: 2026-02-09 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "f8a2b4c6d8e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Canonical category names from CATEGORY_KEYWORDS in app.services.categorize.
# Any category whose name is NOT in this set will be removed.
VALID_CATEGORY_NAMES: set[str] = {
    "Performing Arts",
    "Live Music",
    "Visual Arts",
    "Family & Kids",
    "Food & Drink",
    "Outdoors & Nature",
    "Sports & Fitness",
    "Comedy",
    "Festivals & Fairs",
    "Education & Workshops",
    "Community",
    "Markets & Shopping",
    "Film & Cinema",
    "Holiday & Seasonal",
    "Nightlife",
}


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Discover invalid category IDs
    result = conn.execute(sa.text("SELECT id, name FROM categories"))
    invalid_ids: list[int] = []
    for row in result:
        if row[1] not in VALID_CATEGORY_NAMES:
            invalid_ids.append(row[0])

    if not invalid_ids:
        return

    # 2. Delete event_categories rows referencing invalid categories
    conn.execute(
        sa.text("DELETE FROM event_categories WHERE category_id = ANY(:ids)"),
        {"ids": invalid_ids},
    )

    # 3. Delete the invalid category rows themselves
    conn.execute(
        sa.text("DELETE FROM categories WHERE id = ANY(:ids)"),
        {"ids": invalid_ids},
    )


def downgrade() -> None:
    # Deleted data cannot be restored; this is a one-way cleanup.
    pass
