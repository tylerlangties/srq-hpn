from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TaskRun(Base):
    __tablename__: str = "task_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    task_name: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(32), default="started", index=True)

    queue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    worker_hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    retries: Mapped[int | None] = mapped_column(Integer, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), index=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    runtime_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
