"""add slug to sources

Revision ID: c2f4a8b1d9e3
Revises: 9f4d2b8c6a1e
Create Date: 2026-03-01 06:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c2f4a8b1d9e3"
down_revision: str | Sequence[str] | None = "9f4d2b8c6a1e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("slug", sa.String(length=64), nullable=True))

    op.execute(
        """
        UPDATE sources
        SET slug = 'vanwezel'
        WHERE slug IS NULL
          AND (lower(name) LIKE '%van wezel%' OR lower(url) LIKE '%vanwezel%')
        """
    )
    op.execute(
        """
        UPDATE sources
        SET slug = 'mote'
        WHERE slug IS NULL
          AND (lower(name) LIKE '%mote%' OR lower(url) LIKE '%mote%')
        """
    )
    op.execute(
        """
        UPDATE sources
        SET slug = 'asolorep'
        WHERE slug IS NULL
          AND (lower(name) LIKE '%asolo%' OR lower(url) LIKE '%asolorep%')
        """
    )
    op.execute(
        """
        UPDATE sources
        SET slug = 'artfestival'
        WHERE slug IS NULL
          AND (lower(name) LIKE '%art festival%' OR lower(url) LIKE '%artfestival%')
        """
    )
    op.execute(
        """
        UPDATE sources
        SET slug = 'bigtop'
        WHERE slug IS NULL
          AND (lower(name) LIKE '%big top%' OR lower(url) LIKE '%bigtop%')
        """
    )
    op.execute(
        """
        UPDATE sources
        SET slug = 'bigwaters'
        WHERE slug IS NULL
          AND (
            lower(name) LIKE '%big waters%'
            OR lower(name) LIKE '%bigwaters%'
            OR lower(url) LIKE '%bigwaters%'
          )
        """
    )
    op.execute(
        """
        UPDATE sources
        SET slug = 'sarasotafair'
        WHERE slug IS NULL
          AND (
            lower(name) LIKE '%sarasota fair%'
            OR lower(name) LIKE '%sarasotafair%'
            OR lower(url) LIKE '%sarasotafair%'
          )
        """
    )
    op.execute(
        """
        UPDATE sources
        SET slug = 'selby'
        WHERE slug IS NULL
          AND (lower(name) LIKE '%selby%' OR lower(url) LIKE '%selby%')
        """
    )

    op.execute("UPDATE sources SET slug = 'source-' || id::text WHERE slug IS NULL")

    op.execute(
        """
        WITH dupes AS (
          SELECT slug, min(id) AS keep_id
          FROM sources
          GROUP BY slug
          HAVING count(*) > 1
        )
        UPDATE sources s
        SET slug = s.slug || '-' || s.id::text
        FROM dupes d
        WHERE s.slug = d.slug
          AND s.id <> d.keep_id
        """
    )

    op.create_index("ix_sources_slug", "sources", ["slug"], unique=True)
    op.alter_column(
        "sources", "slug", existing_type=sa.String(length=64), nullable=False
    )


def downgrade() -> None:
    op.drop_index("ix_sources_slug", table_name="sources")
    op.drop_column("sources", "slug")
