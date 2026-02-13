"""
Mote Marine Aquarium collector.

Discovers monthly iCal feed URLs and stores them as source_feeds for later
ingestion.  Each month gets its own feed entry.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy.orm import Session

import app.core.env  # noqa: F401
from app.core.logging import setup_logging
from app.db import SessionLocal
from app.models.source import Source

from .utils import (
    add_common_args,
    add_feed_args,
    add_pagination_args,
    get_http_session,
    upsert_source_feed,
    validate_ical_url,
    write_test_data,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://mote.org"
EVENTS_MONTH_PATH = "/events/month/"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MonthEntry:
    year_month: str
    ical_url: str
    page_url: str
    is_current: bool


# ---------------------------------------------------------------------------
# URL / date helpers
# ---------------------------------------------------------------------------


def _month_start(base: date, months_ahead: int) -> date:
    idx = (base.month - 1) + months_ahead
    year = base.year + (idx // 12)
    month = (idx % 12) + 1
    return date(year, month, 1)


def _build_year_month(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def _build_page_url(*, year_month: str, is_current: bool) -> str:
    if is_current:
        return f"{BASE_URL}{EVENTS_MONTH_PATH}"
    return f"{BASE_URL}{EVENTS_MONTH_PATH}{year_month}/"


def _build_ical_url(*, year_month: str, is_current: bool) -> str:
    page_url = _build_page_url(year_month=year_month, is_current=is_current)
    return f"{page_url}?ical=1"


def generate_month_entries(*, months_ahead: int = 2) -> list[MonthEntry]:
    today = date.today()
    entries: list[MonthEntry] = []

    for offset in range(months_ahead + 1):
        month_date = _month_start(today, offset)
        year_month = _build_year_month(month_date)
        is_current = offset == 0
        entries.append(
            MonthEntry(
                year_month=year_month,
                ical_url=_build_ical_url(year_month=year_month, is_current=is_current),
                page_url=_build_page_url(year_month=year_month, is_current=is_current),
                is_current=is_current,
            )
        )

    return entries


# ---------------------------------------------------------------------------
# Core collector
# ---------------------------------------------------------------------------


def run_collector(
    db: Session,
    source: Source,
    *,
    months_ahead: int = 2,
    max_pages: int = 10,
    validate_ical: bool = False,
    future_only: bool = False,
    categories: str | None = None,
    dry_run: bool = False,
    delay: float = 0.5,
) -> dict[str, Any]:
    """
    Run the Mote Marine collector.

    Callable from both CLI and Celery tasks.
    """
    logger.info(
        "Starting Mote Marine collector",
        extra={
            "source_id": source.id,
            "months_ahead": months_ahead,
            "max_pages": max_pages,
            "dry_run": dry_run,
            "validate_ical": validate_ical,
            "future_only": future_only,
            "categories": categories,
        },
    )

    if max_pages != 10 or future_only:
        logger.info(
            "Some standardized collector flags are accepted but not used by this collector",
            extra={
                "source_id": source.id,
                "max_pages": max_pages,
                "future_only": future_only,
            },
        )

    stats: dict[str, Any] = {
        "source_id": source.id,
        "feeds_considered": 0,
        "feeds_upserted": 0,
        "ical_validated": 0,
        "ical_invalid": 0,
        "errors": 0,
    }

    session = get_http_session(
        headers={"Accept": "text/calendar,text/plain;q=0.9,*/*;q=0.8"},
    )

    entries = generate_month_entries(months_ahead=months_ahead)
    logger.info(
        "Generated month entries",
        extra={
            "source_id": source.id,
            "entries": len(entries),
            "months_ahead": months_ahead,
        },
    )

    dry_run_items: list[dict[str, Any]] = []

    for entry in entries:
        stats["feeds_considered"] += 1
        try:
            if validate_ical:
                if validate_ical_url(entry.ical_url, session):
                    stats["ical_validated"] += 1
                else:
                    stats["ical_invalid"] += 1
                    logger.warning(
                        "iCal URL validation failed, skipping",
                        extra={
                            "source_id": source.id,
                            "ical_url": entry.ical_url,
                            "year_month": entry.year_month,
                        },
                    )
                    continue

            external_id = f"mote:{entry.year_month}"

            upsert_source_feed(
                db,
                source_id=source.id,
                external_id=external_id,
                page_url=entry.page_url,
                ical_url=entry.ical_url,
                categories=categories,
                dry_run=dry_run,
            )
            stats["feeds_upserted"] += 1

            if dry_run:
                dry_run_items.append(
                    {
                        "external_id": external_id,
                        "year_month": entry.year_month,
                        "ical_url": entry.ical_url,
                        "page_url": entry.page_url,
                    }
                )

        except Exception as e:
            stats["errors"] += 1
            logger.error(
                "Error upserting month entry",
                extra={
                    "source_id": source.id,
                    "year_month": entry.year_month,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )

    if not dry_run:
        db.commit()
        logger.info("Database commit successful", extra={"source_id": source.id})
    else:
        write_test_data(
            "mote",
            {
                "source_id": source.id,
                "source_name": source.name,
                "collected_at": datetime.now(UTC).isoformat(),
                "items": dry_run_items,
            },
        )

    stats["status"] = "success"
    logger.info("Mote Marine collector completed", extra=stats)

    return stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    setup_logging()

    parser = argparse.ArgumentParser(
        description="Collect Mote Marine monthly iCal feeds"
    )
    add_common_args(parser)
    add_pagination_args(parser)
    add_feed_args(parser)
    parser.add_argument(
        "--months-ahead",
        type=int,
        default=2,
        help="Number of future months to include (default: 2)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        source = db.get(Source, args.source_id)
        if not source:
            logger.error("Source not found", extra={"source_id": args.source_id})
            raise SystemExit(f"Source {args.source_id} not found")

        run_collector(
            db,
            source,
            months_ahead=args.months_ahead,
            max_pages=args.max_pages,
            validate_ical=args.validate_ical,
            future_only=args.future_only,
            categories=args.categories,
            dry_run=args.dry_run,
            delay=args.delay,
        )

    except Exception as e:
        db.rollback()
        logger.critical(
            "Fatal error in collector",
            extra={
                "source_id": args.source_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
