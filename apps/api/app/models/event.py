from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.event_occurrence import EventOccurrence


class Event(Base):
    __tablename__ = "events"

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
    # Stable identifier for this event within the source (typically the iCal UID from VEVENT).
    # Used for deduplication: unique(source_id, external_id)
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
