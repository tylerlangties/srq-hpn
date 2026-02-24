from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

MAX_EVENTS_PER_BATCH = 500


class BigtopIngestEvent(BaseModel):
    external_id: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    location: str | None = None
    start_utc: datetime
    end_utc: datetime | None = None
    external_url: str | None = None
    categories: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("start_utc", "end_utc")
    @classmethod
    def _timezone_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("datetime must include timezone")
        return value

    @model_validator(mode="after")
    def _validate_range(self) -> BigtopIngestEvent:
        if self.end_utc is not None and self.end_utc < self.start_utc:
            raise ValueError("end_utc must be greater than or equal to start_utc")
        return self


class BigtopIngestRequest(BaseModel):
    source_id: int = Field(..., ge=1)
    run_id: str = Field(..., min_length=1, max_length=120)
    sent_at: datetime
    events: list[BigtopIngestEvent] = Field(
        default_factory=list,
        min_length=1,
        max_length=MAX_EVENTS_PER_BATCH,
    )

    @field_validator("sent_at")
    @classmethod
    def _sent_at_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("sent_at must include timezone")
        return value


class BigtopIngestRejectedEvent(BaseModel):
    external_id: str
    reason: str


class BigtopIngestResponse(BaseModel):
    run_id: str
    source_id: int
    received: int
    upserted: int
    rejected: int
    rejected_events: list[BigtopIngestRejectedEvent] = Field(default_factory=list)
