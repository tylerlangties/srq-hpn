from __future__ import annotations

import logging
from datetime import UTC, datetime

from celery.signals import task_failure, task_postrun, task_prerun
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.task_run import TaskRun

logger = logging.getLogger(__name__)

TERMINAL_FAILURE_STATES = {"failure", "revoked"}


def _normalize_state(state: str | None) -> str:
    if not state:
        return "unknown"
    return state.strip().lower()


def _trim_text(value: object | None, max_len: int = 2000) -> str | None:
    if value is None:
        return None
    text = str(value)
    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}..."


def _get_run(db: Session, task_id: str) -> TaskRun | None:
    return db.scalar(select(TaskRun).where(TaskRun.task_id == task_id))


@task_prerun.connect
def record_task_start(task_id: str | None = None, task=None, **_: object) -> None:
    if task_id is None or task is None:
        return

    delivery_info = getattr(task.request, "delivery_info", None)
    queue = None
    if isinstance(delivery_info, dict):
        queue = delivery_info.get("routing_key") or delivery_info.get("exchange")

    worker_hostname = getattr(task.request, "hostname", None)
    retries = getattr(task.request, "retries", None)
    task_name = getattr(task, "name", "unknown")

    db = SessionLocal()
    try:
        run = _get_run(db, task_id)
        if run is None:
            run = TaskRun(
                task_id=task_id,
                task_name=task_name,
                status="started",
                queue=queue,
                worker_hostname=worker_hostname,
                retries=retries,
                started_at=datetime.now(UTC),
            )
            db.add(run)
        else:
            run.task_name = task_name
            run.status = "started"
            run.queue = queue
            run.worker_hostname = worker_hostname
            run.retries = retries
            run.started_at = datetime.now(UTC)
            run.finished_at = None
            run.runtime_ms = None
            run.error = None
            run.result_preview = None
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to persist task start", extra={"task_id": task_id})
    finally:
        db.close()


@task_postrun.connect
def record_task_end(
    task_id: str | None = None,
    task=None,
    state: str | None = None,
    retval: object | None = None,
    **_: object,
) -> None:
    if task_id is None or task is None:
        return

    normalized_state = _normalize_state(state)
    finished_at = datetime.now(UTC)

    db = SessionLocal()
    try:
        run = _get_run(db, task_id)
        if run is None:
            run = TaskRun(
                task_id=task_id,
                task_name=getattr(task, "name", "unknown"),
                status=normalized_state,
                started_at=finished_at,
            )
            db.add(run)

        run.status = normalized_state
        run.finished_at = finished_at
        run.runtime_ms = int((finished_at - run.started_at).total_seconds() * 1000)

        if normalized_state == "success":
            run.result_preview = _trim_text(retval)
        elif normalized_state in TERMINAL_FAILURE_STATES and run.error is None:
            run.error = _trim_text(retval)

        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "Failed to persist task completion", extra={"task_id": task_id}
        )
    finally:
        db.close()


@task_failure.connect
def record_task_failure(
    task_id: str | None = None,
    exception: BaseException | None = None,
    task=None,
    **_: object,
) -> None:
    if task_id is None:
        return

    finished_at = datetime.now(UTC)
    error_message = _trim_text(exception)

    db = SessionLocal()
    try:
        run = _get_run(db, task_id)
        if run is None:
            run = TaskRun(
                task_id=task_id,
                task_name=getattr(task, "name", "unknown"),
                status="failure",
                started_at=finished_at,
            )
            db.add(run)

        run.status = "failure"
        run.finished_at = finished_at
        run.runtime_ms = int((finished_at - run.started_at).total_seconds() * 1000)
        run.error = error_message
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to persist task failure", extra={"task_id": task_id})
    finally:
        db.close()
