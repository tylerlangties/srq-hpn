from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.source import Source


class SourceFeed(Base):
    __tablename__ = "source_feeds"

    id: Mapped[int] = mapped_column(primary_key=True)

    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    source: Mapped[Source] = relationship(back_populates="feeds")  # type: ignore[name-defined]

    # Stable identifier for this iCal file/feed within the source.
    # Used for deduplication: unique(source_id, external_id)
    # Examples: "mustdo:event-slug", "2025-01" (for monthly feeds), or URL hash
    # NOTE: This is NOT the same as Event.external_id (which is the iCal event UID)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    page_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    ical_url: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="new"
    )  # new|ok|error
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_modified: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Track how many events were parsed/ingested from this iCal file
    # Useful for multi-event iCal files (e.g., monthly feeds with dozens of events)
    events_parsed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    events_ingested: Mapped[int | None] = mapped_column(Integer, nullable=True)

    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Custom categories to apply during ingestion (comma-separated)
    # These are used instead of or in addition to categories from iCal files
    categories: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
