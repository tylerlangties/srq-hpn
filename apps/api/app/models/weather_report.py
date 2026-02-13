from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class WeatherReport(Base):
    __tablename__ = "weather_reports"
    __table_args__ = (
        Index(
            "ix_weather_reports_provider_location_exp_fetch",
            "provider",
            "location_key",
            "expires_at",
            "fetched_at",
        ),
        Index(
            "ix_weather_reports_provider_location_slot_exp_fetch",
            "provider",
            "location_key",
            "slot",
            "expires_at",
            "fetched_at",
        ),
        Index("ix_weather_reports_fetched_at", "fetched_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    location_key: Mapped[str] = mapped_column(String(128), nullable=False)
    slot: Mapped[str] = mapped_column(String(32), nullable=False)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
