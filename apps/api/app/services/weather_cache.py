from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.weather_fetch_counter import WeatherFetchCounter
from app.models.weather_report import WeatherReport

logger = logging.getLogger(__name__)

SRQ_TZ = ZoneInfo("America/New_York")

OPEN_METEO_PROVIDER = "open-meteo"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_LOCATION_KEY = os.getenv("WEATHER_LOCATION_KEY", "sarasota-fl")
WEATHER_LATITUDE = float(os.getenv("WEATHER_LATITUDE", "27.3364"))
WEATHER_LONGITUDE = float(os.getenv("WEATHER_LONGITUDE", "-82.5307"))
WEATHER_CACHE_TTL_HOURS = int(os.getenv("WEATHER_CACHE_TTL_HOURS", "6"))
WEATHER_DAILY_FETCH_CAP = int(os.getenv("WEATHER_DAILY_FETCH_CAP", "25"))
WEATHER_RETENTION_DAYS = int(os.getenv("WEATHER_RETENTION_DAYS", "10"))


@dataclass(frozen=True)
class WeatherSummaryData:
    date: str
    temp: int | None
    condition: str
    icon: str
    sunset: str | None = None


@dataclass(frozen=True)
class WeatherPayloadData:
    today: WeatherSummaryData
    tomorrow: WeatherSummaryData
    weekend: WeatherSummaryData


def _weather_code_to_summary(code: int) -> tuple[str, str]:
    if code == 0:
        return ("clear", "☀️")
    if code <= 2:
        return ("partly cloudy", "⛅")
    if code <= 3:
        return ("cloudy", "☁️")
    if 45 <= code <= 48:
        return ("foggy", "🌫️")
    if 51 <= code <= 67:
        return ("drizzle", "🌦️")
    if 71 <= code <= 77:
        return ("snow", "❄️")
    if 80 <= code <= 82:
        return ("rain", "🌧️")
    if code >= 95:
        return ("stormy", "⛈️")
    return ("pleasant", "🌤️")


def _to_local_time_label(iso_value: str) -> str:
    dt = datetime.fromisoformat(iso_value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=SRQ_TZ)
    local_dt = dt.astimezone(SRQ_TZ)
    return local_dt.strftime("%I:%M %p").lstrip("0")


def _next_weekend_index(dates: list[str]) -> int:
    for index, iso_day in enumerate(dates):
        if date.fromisoformat(iso_day).weekday() == 5:
            return index
    return 2


def _extract_requested_dates(payload: WeatherPayloadData) -> set[date]:
    return {
        date.fromisoformat(payload.today.date),
        date.fromisoformat(payload.tomorrow.date),
        date.fromisoformat(payload.weekend.date),
    }


def _payload_from_reports(
    reports_by_date: dict[date, WeatherReport],
) -> WeatherPayloadData | None:
    if len(reports_by_date) < 3:
        return None

    sorted_dates = sorted(reports_by_date.keys())
    today_date = sorted_dates[0]
    tomorrow_date = sorted_dates[1]
    weekend_date = next((d for d in sorted_dates if d.weekday() == 5), sorted_dates[2])

    today_payload = reports_by_date.get(today_date)
    tomorrow_payload = reports_by_date.get(tomorrow_date)
    weekend_payload = reports_by_date.get(weekend_date)

    if not today_payload or not tomorrow_payload or not weekend_payload:
        return None

    return WeatherPayloadData(
        today=WeatherSummaryData(**today_payload.payload_json),
        tomorrow=WeatherSummaryData(**tomorrow_payload.payload_json),
        weekend=WeatherSummaryData(**weekend_payload.payload_json),
    )


def _reserve_fetch_slot(
    db: Session, *, provider: str, now: datetime
) -> tuple[bool, int]:
    local_day = now.astimezone(SRQ_TZ).date()

    counter_stmt = (
        select(WeatherFetchCounter)
        .where(WeatherFetchCounter.provider == provider)
        .where(WeatherFetchCounter.day == local_day)
        .with_for_update()
    )
    counter = db.scalar(counter_stmt)

    if counter is None:
        counter = WeatherFetchCounter(
            provider=provider,
            day=local_day,
            fetch_count=0,
            last_fetch_at=None,
        )
        db.add(counter)
        db.flush()

    if counter.fetch_count >= WEATHER_DAILY_FETCH_CAP:
        return (False, counter.fetch_count)

    counter.fetch_count += 1
    counter.last_fetch_at = now
    db.commit()
    return (True, counter.fetch_count)


def _fetch_provider_payload() -> WeatherPayloadData:
    params = {
        "latitude": str(WEATHER_LATITUDE),
        "longitude": str(WEATHER_LONGITUDE),
        "daily": "temperature_2m_max,weathercode,sunset",
        "timezone": "America/New_York",
        "temperature_unit": "fahrenheit",
        "forecast_days": "8",
    }

    response = requests.get(OPEN_METEO_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    daily = data.get("daily") or {}
    times = daily.get("time") or []
    temperatures = daily.get("temperature_2m_max") or []
    weather_codes = daily.get("weathercode") or []
    sunsets = daily.get("sunset") or []

    if len(times) < 3 or len(temperatures) < 3 or len(weather_codes) < 3:
        raise ValueError("Weather provider response missing required daily fields")

    def build_summary(index: int) -> WeatherSummaryData:
        condition, icon = _weather_code_to_summary(int(weather_codes[index]))
        raw_temp = temperatures[index]
        temp_value = round(raw_temp) if isinstance(raw_temp, float | int) else None
        sunset_raw = sunsets[index] if index < len(sunsets) else None

        return WeatherSummaryData(
            date=times[index],
            temp=temp_value,
            condition=condition,
            icon=icon,
            sunset=_to_local_time_label(sunset_raw) if sunset_raw else None,
        )

    today = build_summary(0)
    tomorrow = build_summary(1)
    weekend = build_summary(_next_weekend_index(times))

    return WeatherPayloadData(today=today, tomorrow=tomorrow, weekend=weekend)


def _store_payload_snapshot(
    db: Session,
    *,
    provider: str,
    location_key: str,
    payload: WeatherPayloadData,
    now: datetime,
) -> None:
    expires_at = now + timedelta(hours=WEATHER_CACHE_TTL_HOURS)

    for summary in (payload.today, payload.tomorrow, payload.weekend):
        db.add(
            WeatherReport(
                provider=provider,
                location_key=location_key,
                forecast_date=date.fromisoformat(summary.date),
                payload_json={
                    "date": summary.date,
                    "temp": summary.temp,
                    "condition": summary.condition,
                    "icon": summary.icon,
                    "sunset": summary.sunset,
                },
                fetched_at=now,
                expires_at=expires_at,
            )
        )

    db.commit()


def get_weather_payload(
    db: Session,
    *,
    provider: str = OPEN_METEO_PROVIDER,
    location_key: str = WEATHER_LOCATION_KEY,
    force_refresh: bool = False,
) -> WeatherPayloadData:
    now = datetime.now(UTC)

    fresh_stmt = (
        select(WeatherReport)
        .where(WeatherReport.provider == provider)
        .where(WeatherReport.location_key == location_key)
        .where(WeatherReport.expires_at > now)
        .order_by(WeatherReport.fetched_at.desc())
        .limit(3)
    )
    fresh_reports = db.scalars(fresh_stmt).all()

    fresh_by_date: dict[date, WeatherReport] = {}
    for report in fresh_reports:
        fresh_by_date.setdefault(report.forecast_date, report)

    payload = _payload_from_reports(fresh_by_date)
    if payload is not None and not force_refresh:
        logger.info(
            "weather_cache_hit",
            extra={"provider": provider, "location_key": location_key},
        )
        return payload

    can_fetch, fetch_count = _reserve_fetch_slot(db, provider=provider, now=now)
    if can_fetch:
        try:
            fetched_payload = _fetch_provider_payload()
        except Exception:
            logger.exception(
                "weather_fetch_failed",
                extra={"provider": provider, "location_key": location_key},
            )
            fetched_payload = None
        else:
            _store_payload_snapshot(
                db,
                provider=provider,
                location_key=location_key,
                payload=fetched_payload,
                now=now,
            )
            logger.info(
                "weather_fetch_performed",
                extra={
                    "provider": provider,
                    "location_key": location_key,
                    "fetch_count_today": fetch_count,
                },
            )
            return fetched_payload
    else:
        logger.warning(
            "weather_fetch_skipped_cap",
            extra={
                "provider": provider,
                "location_key": location_key,
                "fetch_count_today": fetch_count,
                "daily_cap": WEATHER_DAILY_FETCH_CAP,
            },
        )

    stale_stmt = (
        select(WeatherReport)
        .where(WeatherReport.provider == provider)
        .where(WeatherReport.location_key == location_key)
        .order_by(WeatherReport.fetched_at.desc())
        .limit(12)
    )
    stale_reports = db.scalars(stale_stmt).all()
    stale_by_date: dict[date, WeatherReport] = {}
    for report in stale_reports:
        stale_by_date.setdefault(report.forecast_date, report)

    stale_payload = _payload_from_reports(stale_by_date)
    if stale_payload is not None:
        logger.warning(
            "weather_serving_stale_cache",
            extra={"provider": provider, "location_key": location_key},
        )
        return stale_payload

    raise RuntimeError("Weather data unavailable")


def refresh_weather_cache(
    db: Session,
    *,
    provider: str = OPEN_METEO_PROVIDER,
    location_key: str = WEATHER_LOCATION_KEY,
) -> dict[str, Any]:
    payload = get_weather_payload(
        db,
        provider=provider,
        location_key=location_key,
        force_refresh=True,
    )
    days = sorted(_extract_requested_dates(payload))
    return {
        "provider": provider,
        "location_key": location_key,
        "dates": [day.isoformat() for day in days],
    }


def prune_old_weather_reports(db: Session) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=WEATHER_RETENTION_DAYS)
    count_stmt = select(func.count(WeatherReport.id)).where(
        WeatherReport.fetched_at < cutoff
    )
    delete_count = db.scalar(count_stmt) or 0
    stmt = delete(WeatherReport).where(WeatherReport.fetched_at < cutoff)
    db.execute(stmt)
    db.commit()
    return delete_count
