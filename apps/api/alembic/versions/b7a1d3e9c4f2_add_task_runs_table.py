from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b7a1d3e9c4f2"
down_revision: str | Sequence[str] | None = "e4f9b7c2d1a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "task_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("task_name", sa.String(length=255), nullable=False),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="started"
        ),
        sa.Column("queue", sa.String(length=255), nullable=True),
        sa.Column("worker_hostname", sa.String(length=255), nullable=True),
        sa.Column("retries", sa.Integer(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("runtime_ms", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("result_preview", sa.Text(), nullable=True),
        sa.UniqueConstraint("task_id", name="uq_task_runs_task_id"),
    )

    op.create_index("ix_task_runs_task_id", "task_runs", ["task_id"])
    op.create_index("ix_task_runs_task_name", "task_runs", ["task_name"])
    op.create_index("ix_task_runs_status", "task_runs", ["status"])
    op.create_index("ix_task_runs_started_at", "task_runs", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_task_runs_started_at", table_name="task_runs")
    op.drop_index("ix_task_runs_status", table_name="task_runs")
    op.drop_index("ix_task_runs_task_name", table_name="task_runs")
    op.drop_index("ix_task_runs_task_id", table_name="task_runs")
    op.drop_table("task_runs")
