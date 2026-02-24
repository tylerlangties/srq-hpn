from __future__ import annotations

import argparse
import logging
import os
import socket
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import requests

import app.core.env  # noqa: F401
from app.collectors.bigtop import (
    DEFAULT_CREATED_MONTHS,
    _parse_created_at,
    build_ical_url,
    build_page_url,
    establish_session,
    fetch_events,
)
from app.core.logging import setup_logging
from app.ingestion.ical import fetch_ics, parse_ics

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
DEFAULT_BATCH_SIZE = 250


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())


def _make_signature(title: str | None, start_utc: datetime) -> tuple[str, datetime]:
    return (_normalize_text(title), start_utc)


def _build_run_id() -> str:
    hostname = socket.gethostname().split(".")[0]
    return f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{hostname}"


def _chunked(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _post_with_retries(
    *,
    session: requests.Session,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: int,
    retries: int,
) -> requests.Response:
    last_exc: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            resp = session.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code >= 500 and attempt < retries:
                time.sleep(attempt)
                continue
            return resp
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(attempt)
                continue
            raise

    if last_exc:
        raise last_exc
    raise RuntimeError("Unexpected retry state")


def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Push Big Top events from local machine to production ingest bridge"
    )
    parser.add_argument(
        "--api-base",
        default=os.getenv("BIGTOP_INGEST_API_BASE"),
        help="Production API base URL, e.g. https://srqhappenings.com",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("BIGTOP_INGEST_TOKEN"),
        help="Ingest bridge bearer token",
    )
    parser.add_argument("--source-id", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    parser.add_argument("--delay", type=float, default=0.25)
    parser.add_argument(
        "--future-only",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--created-months",
        type=int,
        default=DEFAULT_CREATED_MONTHS,
        help="Only include events with createdAt in this recent month window",
    )
    parser.add_argument(
        "--categories",
        default=None,
        help="Comma-separated categories to attach to pushed events",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.api_base:
        raise SystemExit("--api-base (or BIGTOP_INGEST_API_BASE) is required")
    if not args.token:
        raise SystemExit("--token (or BIGTOP_INGEST_TOKEN) is required")
    if args.batch_size < 1 or args.batch_size > 500:
        raise SystemExit("--batch-size must be between 1 and 500")

    ingest_url = args.api_base.rstrip("/") + "/api/ingest/bigtop/events"
    created_cutoff = datetime.now(UTC) - timedelta(days=args.created_months * 30)
    categories = [c.strip() for c in (args.categories or "").split(",") if c.strip()]

    logger.info(
        "Starting local Big Top push",
        extra={
            "api_base": args.api_base,
            "source_id": args.source_id,
            "future_only": args.future_only,
            "created_months": args.created_months,
            "batch_size": args.batch_size,
            "dry_run": args.dry_run,
        },
    )

    scrape_session = requests.Session()
    establish_session(scrape_session)
    events = fetch_events(scrape_session)

    if args.future_only:
        before = len(events)
        filtered: list[dict[str, Any]] = []
        for ev in events:
            created_at = _parse_created_at(ev.get("createdAt"))
            if created_at is None or created_at >= created_cutoff:
                filtered.append(ev)
        events = filtered
        logger.info(
            "Applied createdAt cutoff",
            extra={
                "before": before,
                "after": len(events),
                "cutoff": created_cutoff.isoformat(),
            },
        )

    pushed_events: list[dict[str, Any]] = []
    seen_signatures: set[tuple[str, datetime]] = set()

    for idx, ev in enumerate(events, start=1):
        slug = ev.get("slug")
        if not slug:
            continue

        try:
            ics_bytes = fetch_ics(build_ical_url(slug), session=scrape_session)
            parsed = parse_ics(ics_bytes)
        except Exception as exc:
            logger.warning(
                "Skipping feed due to fetch/parse error",
                extra={
                    "slug": slug,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            continue

        for parsed_event in parsed:
            signature = _make_signature(parsed_event.summary, parsed_event.start_utc)
            if signature in seen_signatures:
                continue

            pushed_events.append(
                {
                    "external_id": parsed_event.uid,
                    "title": parsed_event.summary,
                    "description": parsed_event.description,
                    "location": parsed_event.location,
                    "start_utc": parsed_event.start_utc.isoformat(),
                    "end_utc": parsed_event.end_utc.isoformat()
                    if parsed_event.end_utc is not None
                    else None,
                    "external_url": parsed_event.url or build_page_url(slug),
                    "categories": categories,
                }
            )
            seen_signatures.add(signature)

        if idx < len(events) and args.delay > 0:
            time.sleep(args.delay)

    if not pushed_events:
        logger.info("No events to push")
        return

    logger.info(
        "Prepared events for upload",
        extra={
            "events": len(pushed_events),
            "batches": len(_chunked(pushed_events, args.batch_size)),
        },
    )

    if args.dry_run:
        logger.info("Dry run complete; not sending to production")
        return

    run_id = _build_run_id()
    headers = {
        "Authorization": f"Bearer {args.token}",
        "Content-Type": "application/json",
    }

    send_session = requests.Session()
    totals = {"received": 0, "upserted": 0, "rejected": 0}

    for i, batch in enumerate(_chunked(pushed_events, args.batch_size), start=1):
        payload = {
            "source_id": args.source_id,
            "run_id": run_id,
            "sent_at": datetime.now(UTC).isoformat(),
            "events": batch,
        }
        response = _post_with_retries(
            session=send_session,
            url=ingest_url,
            headers=headers,
            payload=payload,
            timeout=args.timeout,
            retries=args.retries,
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"Batch {i} failed with {response.status_code}: {response.text[:500]}"
            )

        data = response.json()
        totals["received"] += int(data.get("received", 0))
        totals["upserted"] += int(data.get("upserted", 0))
        totals["rejected"] += int(data.get("rejected", 0))

        logger.info(
            "Uploaded batch",
            extra={
                "batch_index": i,
                "batch_size": len(batch),
                "received": data.get("received", 0),
                "upserted": data.get("upserted", 0),
                "rejected": data.get("rejected", 0),
            },
        )

    logger.info("Local Big Top push complete", extra={"run_id": run_id, **totals})


if __name__ == "__main__":
    main()
