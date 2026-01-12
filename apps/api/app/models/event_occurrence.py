from datetime import datetime
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


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

    # 🔹 ORM relationship
    event: Mapped["Event"] = relationship(back_populates="occurrences")
