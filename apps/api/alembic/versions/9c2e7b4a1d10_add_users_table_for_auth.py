"""add users table for auth

Revision ID: 9c2e7b4a1d10
Revises: b5d7e9f1a3c6
Create Date: 2026-02-11 11:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9c2e7b4a1d10"
down_revision: str | Sequence[str] | None = "b5d7e9f1a3c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            server_default="user",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column(
            "auth_provider",
            sa.String(length=32),
            nullable=False,
            server_default="local",
        ),
        sa.Column("provider_user_id", sa.String(length=255), nullable=True),
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
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("role IN ('admin', 'user')", name="ck_users_role"),
    )

    op.create_index("uq_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.execute(
        """
        CREATE UNIQUE INDEX uq_users_provider_identity
        ON users (auth_provider, provider_user_id)
        WHERE provider_user_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_index("uq_users_provider_identity", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("uq_users_email", table_name="users")
    op.drop_table("users")
