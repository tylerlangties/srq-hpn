from pydantic import BaseModel


class WeatherSummaryOut(BaseModel):
    date: str
    temp: int | None
    condition: str
    icon: str
    sunset: str | None = None


class WeatherPayloadOut(BaseModel):
    today: WeatherSummaryOut
    tomorrow: WeatherSummaryOut
    weekend: WeatherSummaryOut
