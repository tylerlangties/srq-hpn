from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.event_occurrence import EventOccurrence


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        # Partial unique index: prevents duplicate (source_id, external_id)
        # pairs while allowing multiple rows where external_id IS NULL.
        Index(
            "uq_events_source_external_id",
            "source_id",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    venue_id: Mapped[int | None] = mapped_column(
        ForeignKey("venues.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    is_free: Mapped[bool] = mapped_column(default=False)
    price_text: Mapped[str | None] = mapped_column(String(50), nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), default="scheduled"
    )  # scheduled|canceled
    # When True, event is excluded from public API (e.g. not local enough).
    # Preserved across re-ingestion.
    hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    # Stable identifier for this event within the source (typically the iCal UID from VEVENT).
    # Used for deduplication: unique(source_id, external_id) — enforced by
    # the partial unique index uq_events_source_external_id.
    # NOTE: This is NOT the same as SourceFeed.external_id (which identifies the iCal file/feed)
    external_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    external_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # 🔹 ORM relationships
    # Venue relationship removed, venue is now on EventOccurrence
    # venue: Mapped["Venue"] = relationship(back_populates="events")
    occurrences: Mapped[list["EventOccurrence"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    categories: Mapped[list["Category"]] = relationship(
        secondary="event_categories",
        back_populates="events",
    )
