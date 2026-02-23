from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class VenueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    area: str | None = None


class VenueDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    area: str | None = None
    address: str | None = None
    website: str | None = None
    description: str | None = None
    hero_image_path: str | None = None
    timezone: str | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    description: str | None = None
    is_free: bool
    price_text: str | None = None
    external_url: str | None = None
    status: str
    categories: list[CategoryOut] = Field(default_factory=list)


class EventOccurrenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_datetime_utc: datetime
    end_datetime_utc: datetime | None = None

    location_text: str | None = None
    venue: VenueOut | None = None

    event: EventOut


class EventCountOut(BaseModel):
    count: int
    start: date
    end: date
    timezone: str = "America/New_York"


class EventDetailOut(BaseModel):
    event: EventOut
    next_occurrence: EventOccurrenceOut
    upcoming_occurrences: list[EventOccurrenceOut] = Field(default_factory=list)
    more_from_venue: list[EventOccurrenceOut] = Field(default_factory=list)


class EventSlugResolutionOut(BaseModel):
    event_id: int
    canonical_segment: str
    is_unique: bool
