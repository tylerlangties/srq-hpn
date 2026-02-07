"""
Shared utilities for event collectors.

This module provides common functions used across multiple collectors to reduce
duplication and keep individual collector files focused on site-specific logic.

Provides:
- HTTP session factory with retry logic
- HTML fetching with logging
- iCal URL validation and future-date checking
- Source feed upsert (for iCal-based collectors)
- Dry run test data output
- Common CLI argument helpers
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from urllib3.util.retry import Retry

from app.models.source_feed import SourceFeed

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

TEST_DATA_DIR = Path(__file__).parent / "test_data"

# Regex to extract dates from iCal content (DTSTART, RDATE, etc.)
_ICAL_DATE_RE = re.compile(r"(\d{8}T\d{6}Z?)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def get_http_session(
    *,
    headers: dict[str, str] | None = None,
    allowed_methods: list[str] | None = None,
) -> requests.Session:
    """
    Create an HTTP session with retry logic.

    Args:
        headers: Extra headers to merge with DEFAULT_HEADERS.
        allowed_methods: HTTP methods to retry on (default: HEAD, GET).
    """
    session = requests.Session()
    merged = {**DEFAULT_HEADERS}
    if headers:
        merged.update(headers)
    session.headers.update(merged)

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=allowed_methods or ["HEAD", "GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def fetch_html(session: requests.Session, url: str, *, timeout: int = 30) -> str:
    """Fetch HTML content from *url* and return the response body."""
    logger.debug("Fetching HTML", extra={"url": url})
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    logger.debug(
        "HTML fetched",
        extra={"url": url, "status": resp.status_code, "length": len(resp.text)},
    )
    return resp.text


# ---------------------------------------------------------------------------
# iCal helpers (used by feed-based collectors)
# ---------------------------------------------------------------------------


def validate_ical_url(url: str, session: requests.Session) -> bool:
    """Return *True* if *url* responds with HTTP 200 on a HEAD request."""
    try:
        logger.debug("Validating iCal URL", extra={"ical_url": url})
        resp = session.head(url, timeout=10, allow_redirects=True)
        is_valid = resp.status_code == 200
        logger.debug(
            "iCal URL validation result",
            extra={
                "ical_url": url,
                "status_code": resp.status_code,
                "is_valid": is_valid,
            },
        )
        return is_valid
    except Exception as e:
        logger.debug(
            "iCal URL validation failed",
            extra={
                "ical_url": url,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        return False


def _parse_ical_date(date_str: str) -> datetime:
    """Parse an iCal date string like ``20260115T200000Z`` to a *datetime*."""
    if date_str.endswith("Z"):
        return datetime.strptime(date_str, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    if "T" in date_str:
        return datetime.strptime(date_str, "%Y%m%dT%H%M%S").replace(tzinfo=UTC)
    return datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=UTC)


def is_future_event(url: str, session: requests.Session) -> bool:
    """
    Fetch an iCal feed and return *True* if any occurrence is in the future.

    If the feed cannot be fetched or parsed, returns *True* (include by default).
    """
    try:
        logger.debug("Checking if event is in future", extra={"ical_url": url})
        resp = session.get(url, timeout=15)
        resp.raise_for_status()

        all_dates = _ICAL_DATE_RE.findall(resp.text)
        if not all_dates:
            logger.debug(
                "No dates found in iCal, assuming future event", extra={"ical_url": url}
            )
            return True

        now = datetime.now(UTC)
        future_dates = []
        for ds in all_dates:
            try:
                if _parse_ical_date(ds) >= now:
                    future_dates.append(ds)
            except ValueError:
                continue

        is_future = len(future_dates) > 0
        logger.debug(
            "Event date check",
            extra={
                "ical_url": url,
                "total_dates_found": len(all_dates),
                "future_dates_count": len(future_dates),
                "is_future": is_future,
            },
        )
        return is_future

    except Exception as e:
        logger.debug(
            "Failed to check event date, assuming future event",
            extra={
                "ical_url": url,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        return True


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def upsert_source_feed(
    db: Session,
    *,
    source_id: int,
    external_id: str,
    page_url: str,
    ical_url: str,
    categories: str | None = None,
    dry_run: bool = False,
) -> None:
    """
    Upsert a row in the ``source_feeds`` table.

    Used by iCal-based collectors to register discovered feed URLs for
    later ingestion.
    """
    now = datetime.now(UTC)

    if dry_run:
        logger.debug(
            "DRY RUN: Would upsert source feed",
            extra={
                "source_id": source_id,
                "external_id": external_id,
                "ical_url": ical_url,
                "page_url": page_url,
                "categories": categories,
            },
        )
        return

    values: dict[str, Any] = {
        "source_id": source_id,
        "external_id": external_id,
        "page_url": page_url,
        "ical_url": ical_url,
        "status": "new",
        "last_seen_at": now,
        "updated_at": now,
    }
    update_set: dict[str, Any] = {
        "page_url": page_url,
        "ical_url": ical_url,
        "last_seen_at": now,
        "updated_at": now,
    }
    if categories is not None:
        values["categories"] = categories
        update_set["categories"] = categories

    stmt = (
        insert(SourceFeed)
        .values(**values)
        .on_conflict_do_update(
            constraint="uq_source_feeds_source_external_id",
            set_=update_set,
        )
    )
    db.execute(stmt)
    logger.debug(
        "Upserted source feed",
        extra={
            "source_id": source_id,
            "external_id": external_id,
            "ical_url": ical_url,
        },
    )


# ---------------------------------------------------------------------------
# Dry-run / test-data helpers
# ---------------------------------------------------------------------------


def write_test_data(collector_name: str, data: dict[str, Any]) -> Path:
    """
    Write dry-run data to ``test_data/{collector_name}.json``.

    Creates the ``test_data/`` directory if it doesn't exist.
    Returns the path of the written file.
    """
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = TEST_DATA_DIR / f"{collector_name}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, default=str)
    logger.info(
        "Test data written",
        extra={
            "path": str(output_path),
            "collector": collector_name,
            "items": len(data.get("items", [])),
        },
    )
    return output_path


# ---------------------------------------------------------------------------
# CLI argument helpers
# ---------------------------------------------------------------------------


def add_common_args(parser: Any, *, default_delay: float = 0.5) -> None:
    """Add ``--source-id``, ``--dry-run``, and ``--delay`` to *parser*."""
    parser.add_argument(
        "--source-id", type=int, required=True, help="Source ID from database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write to database, just simulate collection",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=default_delay,
        help=f"Delay between requests in seconds (default: {default_delay})",
    )


def add_pagination_args(parser: Any, *, default_max_pages: int = 10) -> None:
    """Add ``--max-pages`` to *parser*."""
    parser.add_argument(
        "--max-pages",
        type=int,
        default=default_max_pages,
        help=f"Maximum pages to fetch (default: {default_max_pages})",
    )


def add_feed_args(parser: Any) -> None:
    """Add ``--validate-ical``, ``--future-only``, and ``--categories`` to *parser*."""
    parser.add_argument(
        "--validate-ical",
        action="store_true",
        help="Validate iCal URLs are accessible before storing",
    )
    parser.add_argument(
        "--future-only",
        action="store_true",
        help="Only include events with future dates (fetches each iCal to check)",
    )
    parser.add_argument(
        "--categories",
        type=str,
        help="Comma-separated list of custom categories to attach to events",
    )
