from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.source import Source


class SourceItem(Base):
    __tablename__ = "source_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    source: Mapped[Source] = relationship(back_populates="items")  # type: ignore[name-defined]

    external_id: Mapped[str] = mapped_column(String(255))
    page_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    ical_url: Mapped[str] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(32), default="new")  # new|ok|error
    last_seen_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_fetched_at: Mapped[datetime | None] = mapped_column(nullable=True)

    etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_modified: Mapped[str | None] = mapped_column(String(255), nullable=True)

    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
