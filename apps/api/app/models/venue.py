from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.event_occurrence import EventOccurrence
    from app.models.venue_alias import VenueAlias


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    area: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    hero_image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    timezone: Mapped[str] = mapped_column(String(64), default="America/New_York")
    # 🔹 ORM relationship
    occurrences: Mapped[list["EventOccurrence"]] = relationship(back_populates="venue")
    aliases: Mapped[list["VenueAlias"]] = relationship(
        back_populates="venue",
        cascade="all, delete-orphan",
    )
