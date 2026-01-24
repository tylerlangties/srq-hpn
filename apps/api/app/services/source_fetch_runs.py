from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.source_fetch_run import SourceFetchRun


def start_run(db: Session, *, source_id: int, fetch_url: str) -> SourceFetchRun:
    run = SourceFetchRun(
        source_id=source_id,
        fetch_url=fetch_url,
        started_at=datetime.now(UTC),
        status="running",
    )
    db.add(run)
    db.flush()
    return run


def finish_ok(
    db: Session,
    run: SourceFetchRun,
    *,
    http_status: int | None = None,
    content_type: str | None = None,
    bytes_: int | None = None,
    etag: str | None = None,
    last_modified: str | None = None,
    events_parsed: int | None = None,
    events_ingested: int | None = None,
) -> None:
    run.finished_at = datetime.now(UTC)
    run.status = "ok"
    run.http_status = http_status
    run.content_type = content_type
    run.bytes = bytes_
    run.etag = etag
    run.last_modified = last_modified
    run.events_parsed = events_parsed
    run.events_ingested = events_ingested
    run.error = None
    db.flush()


def finish_error(
    db: Session, run: SourceFetchRun, *, error: str, http_status: int | None = None
) -> None:
    run.finished_at = datetime.now(UTC)
    run.status = "error"
    run.http_status = http_status
    run.error = error
    db.flush()
