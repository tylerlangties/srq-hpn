from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VenueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    area: str | None = None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    is_free: bool
    price_text: str | None = None
    status: str


class EventOccurrenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_datetime_utc: datetime
    end_datetime_utc: datetime | None = None

    location_text: str | None = None
    venue: VenueOut | None = None

    event: EventOut
