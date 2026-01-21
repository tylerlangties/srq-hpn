from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.venue import Venue


class VenueAlias(Base):
    __tablename__ = "venue_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id", ondelete="CASCADE"),
        index=True,
    )

    alias: Mapped[str] = mapped_column(Text)
    alias_normalized: Mapped[str] = mapped_column(Text, unique=True, index=True)

    # make sure this is right later, compare to other models
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    venue: Mapped[Venue] = relationship(back_populates="aliases")
