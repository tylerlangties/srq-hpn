from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.source_feed import SourceFeed


from app.db import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(50))  # e.g. "ical", "rss", "html"
    url: Mapped[str] = mapped_column(Text)
    # Comma-separated category names applied to *all* events from this source.
    # Example: "Performing Arts,Live Music"
    default_categories: Mapped[str | None] = mapped_column(Text, nullable=True)
    feeds: Mapped[list["SourceFeed"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
