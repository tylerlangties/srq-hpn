from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.venue import Venue


class EventOccurrence(Base):
    __tablename__ = "event_occurrences"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)

    start_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True
    )
    end_datetime_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    location_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    venue_id: Mapped[int | None] = mapped_column(
        ForeignKey("venues.id", ondelete="SET NULL"),
        nullable=True,
    )

    # 🔹 ORM relationship
    event: Mapped["Event"] = relationship(back_populates="occurrences")
    venue: Mapped["Venue | None"] = relationship(back_populates="occurrences")
