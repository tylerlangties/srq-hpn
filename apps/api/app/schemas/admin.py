from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UnresolvedLocationGroup(BaseModel):
    """Group of occurrences with the same location_text."""

    location_text: str
    normalized_location: str
    occurrence_count: int
    sample_occurrence_ids: list[int]


class UnresolvedOccurrenceOut(BaseModel):
    """Occurrence with unresolved venue."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    start_datetime_utc: datetime
    end_datetime_utc: datetime | None
    location_text: str | None
    event_id: int
    event_title: str


class LinkOccurrenceRequest(BaseModel):
    """Request to link an occurrence to an existing venue."""

    occurrence_id: int
    venue_id: int


class CreateVenueFromLocationRequest(BaseModel):
    """Request to create a new venue from location text."""

    location_text: str
    name: str
    area: str | None = None
    address: str | None = None


class VenueOut(BaseModel):
    """Venue output schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    area: str | None = None


class AddAliasRequest(BaseModel):
    """Request to add an alias to a venue."""

    alias: str
