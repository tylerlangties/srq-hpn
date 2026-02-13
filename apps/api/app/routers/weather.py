import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.weather import WeatherPayloadOut
from app.services.weather_cache import get_weather_payload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("", response_model=WeatherPayloadOut)
def weather_summary(
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        payload = get_weather_payload(db)
    except RuntimeError as exc:
        logger.error("weather_data_unavailable", exc_info=True)
        raise HTTPException(status_code=503, detail="Weather data unavailable") from exc

    return {
        "today": payload.today.__dict__,
        "tomorrow": payload.tomorrow.__dict__,
        "weekend": payload.weekend.__dict__,
    }
