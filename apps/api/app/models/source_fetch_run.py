from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.source import Source


class SourceFetchRun(Base):
    __tablename__ = "source_fetch_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    source: Mapped[Source] = relationship(back_populates="fetch_runs")  # type: ignore[name-defined]

    fetch_url: Mapped[str] = mapped_column(Text)

    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)

    status: Mapped[str] = mapped_column(
        String(32), default="running"
    )  # running|ok|error|not_modified|skipped

    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    etag: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_modified: Mapped[str | None] = mapped_column(Text, nullable=True)

    events_parsed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    events_ingested: Mapped[int | None] = mapped_column(Integer, nullable=True)

    error: Mapped[str | None] = mapped_column(Text, nullable=True)
