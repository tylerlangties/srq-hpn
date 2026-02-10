"""populate source default_categories

Revision ID: f8a2b4c6d8e0
Revises: e7f1a2b3c4d5
Create Date: 2026-02-08 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f8a2b4c6d8e0"
down_revision: str | Sequence[str] | None = "e7f1a2b3c4d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Source name (case-insensitive ILIKE match) → default_categories value.
# These are the blanket categories always applied to events from each source,
# on top of whatever keyword inference produces per-event.
#
# Source names / IDs (for reference):
#   1 - Van Wezel Performing Arts Hall
#   2 - Mote Marine Laboratory and Aquarium
#   3 - ArtFestival.com
#   4 - Asolo Repertory Theatre
#   5 - Big Top Brewing
#   6 - Big Waters Land Trust
#   7 - Sarasota Fair
#   8 - Selby Gardens
SOURCE_CATEGORIES: dict[str, str] = {
    "Van Wezel Performing Arts Hall": "Performing Arts",
    "Mote Marine Laboratory and Aquarium": "Outdoors & Nature,Family & Kids",
    "ArtFestival.com": "Visual Arts,Festivals & Fairs",
    "Asolo Repertory Theatre": "Performing Arts",
    "Big Top Brewing": "Live Music,Food & Drink",
    "Big Waters Land Trust": "Outdoors & Nature,Community",
    "Sarasota Fair": "Festivals & Fairs,Family & Kids",
    "Selby Gardens": "Outdoors & Nature",
}


def upgrade() -> None:
    for name_pattern, categories in SOURCE_CATEGORIES.items():
        op.execute(
            f"UPDATE sources "
            f"SET default_categories = '{categories}' "
            f"WHERE name ILIKE '%{name_pattern}%' "
            f"AND default_categories IS NULL"
        )


def downgrade() -> None:
    for name_pattern in SOURCE_CATEGORIES:
        op.execute(
            f"UPDATE sources "
            f"SET default_categories = NULL "
            f"WHERE name ILIKE '%{name_pattern}%'"
        )
