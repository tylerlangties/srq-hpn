from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class WeatherFetchCounter(Base):
    __tablename__ = "weather_fetch_counters"
    __table_args__ = (
        UniqueConstraint(
            "provider", "day", name="uq_weather_fetch_counters_provider_day"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    day: Mapped[date] = mapped_column(Date, nullable=False)
    fetch_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_fetch_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
