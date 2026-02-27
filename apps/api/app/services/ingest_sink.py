from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol

import requests

if TYPE_CHECKING:
    from app.models.source import Source


@dataclass(frozen=True)
class IngestEventPayload:
    external_id: str
    title: str
    description: str | None
    location: str | None
    start_utc: datetime
    end_utc: datetime | None
    external_url: str | None
    categories: list[str]


class IngestEventSink(Protocol):
    def on_event(self, *, source: Source, event: IngestEventPayload) -> None: ...

    def flush(self) -> None: ...


class DbSink:
    def on_event(self, *, source: Source, event: IngestEventPayload) -> None:
        return None

    def flush(self) -> None:
        return None


class MultiSink:
    def __init__(self, sinks: list[IngestEventSink]):
        self._sinks = sinks

    def on_event(self, *, source: Source, event: IngestEventPayload) -> None:
        for sink in self._sinks:
            sink.on_event(source=source, event=event)

    def flush(self) -> None:
        for sink in self._sinks:
            sink.flush()


class ProdApiSink:
    def __init__(
        self,
        *,
        api_base: str,
        token: str,
        batch_size: int = 100,
        timeout_seconds: int = 30,
        retries: int = 3,
        run_id: str | None = None,
    ):
        if batch_size < 1 or batch_size > 500:
            raise ValueError("batch_size must be between 1 and 500")
        if retries < 1:
            raise ValueError("retries must be >= 1")

        self._url = api_base.rstrip("/") + "/api/ingest/bigtop/events"
        self._timeout_seconds = timeout_seconds
        self._retries = retries
        self._batch_size = batch_size
        self._run_id = run_id or _build_run_id()
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self._session = requests.Session()
        self._buffer: list[dict] = []
        self._source_id: int | None = None

        self.received = 0
        self.upserted = 0
        self.rejected = 0

    @property
    def run_id(self) -> str:
        return self._run_id

    def on_event(self, *, source: Source, event: IngestEventPayload) -> None:
        if self._source_id is None:
            self._source_id = source.id
        elif self._source_id != source.id:
            raise ValueError("ProdApiSink only supports a single source per run")

        self._buffer.append(
            {
                "external_id": event.external_id,
                "title": event.title,
                "description": event.description,
                "location": event.location,
                "start_utc": event.start_utc.isoformat(),
                "end_utc": event.end_utc.isoformat() if event.end_utc else None,
                "external_url": event.external_url,
                "categories": event.categories,
            }
        )
        if len(self._buffer) >= self._batch_size:
            self._flush_buffer()

    def flush(self) -> None:
        self._flush_buffer()

    def _flush_buffer(self) -> None:
        if not self._buffer:
            return
        if self._source_id is None:
            return

        payload = {
            "source_id": self._source_id,
            "run_id": self._run_id,
            "sent_at": datetime.now(UTC).isoformat(),
            "events": self._buffer,
        }
        response = self._post_with_retries(payload=payload)
        if response.status_code >= 400:
            raise RuntimeError(
                f"ProdApiSink request failed with {response.status_code}: {response.text[:400]}"
            )

        data = response.json()
        self.received += int(data.get("received", 0))
        self.upserted += int(data.get("upserted", 0))
        self.rejected += int(data.get("rejected", 0))
        self._buffer = []

    def _post_with_retries(self, *, payload: dict) -> requests.Response:
        last_exc: Exception | None = None
        for attempt in range(1, self._retries + 1):
            try:
                response = self._session.post(
                    self._url,
                    headers=self._headers,
                    json=payload,
                    timeout=self._timeout_seconds,
                )
                if response.status_code >= 500 and attempt < self._retries:
                    time.sleep(attempt)
                    continue
                return response
            except requests.RequestException as exc:
                last_exc = exc
                if attempt < self._retries:
                    time.sleep(attempt)
                    continue
                raise

        if last_exc:
            raise last_exc
        raise RuntimeError("Unexpected retry state")


def _build_run_id() -> str:
    hostname = socket.gethostname().split(".")[0]
    return f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{hostname}"
