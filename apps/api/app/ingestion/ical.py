from __future__ import annotations

import logging
import random
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from datetime import time as dt_time
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import recurring_ical_events  # type: ignore[import-untyped]
import requests
from icalendar import Calendar  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


# =============================================================================
# iCal Sanitization for Popmenu/Big Top Brewing
# =============================================================================
#
# Problem: Popmenu's iCal export for recurring events outputs malformed data:
#
#   1. Invalid DTEND: "DTEND:-47120101T235959"
#      - This appears to be their placeholder for "no end date"
#      - Year -4712 is invalid and breaks iCal parsers
#
#   2. Empty UNTIL in RRULE: "RRULE:FREQ=WEEKLY;UNTIL=;BYDAY=TH"
#      - The UNTIL parameter is present but has no value
#      - This breaks recurring event expansion
#
# Impact: The recurring_ical_events library silently returns 0 occurrences
# when it encounters this malformed data (no exception, just empty results).
#
# Solution: Pre-process the iCal bytes to remove/fix these issues before
# parsing. This allows recurring events to work correctly.
#
# Source: Discovered while implementing Big Top Brewing scraper (Jan 2026)
# =============================================================================

# Matches the bogus DTEND line that Popmenu outputs for recurring events
# Example: "DTEND:-47120101T235959"
_BOGUS_DTEND_RE = re.compile(rb"^DTEND:-\d+T\d+\r?\n", re.MULTILINE)

# Matches empty UNTIL= in RRULE (with nothing after the = before ; or newline)
# Example: "RRULE:FREQ=WEEKLY;UNTIL=;BYDAY=TH" -> "RRULE:FREQ=WEEKLY;BYDAY=TH"
_EMPTY_UNTIL_RE = re.compile(rb"UNTIL=;")


def _sanitize_popmenu_ical(ics_bytes: bytes) -> bytes:
    """
    Sanitize malformed iCal data from Popmenu before parsing.

    Fixes two known issues with Popmenu's iCal export:
    1. Removes invalid DTEND lines with bogus dates (e.g., DTEND:-47120101T235959)
    2. Removes empty UNTIL= parameters from RRULE lines

    Without this sanitization, recurring events from sources like Big Top Brewing
    will parse successfully but return 0 occurrences because the
    recurring_ical_events library can't process the malformed dates.

    Args:
        ics_bytes: Raw iCal bytes that may contain malformed data

    Returns:
        Sanitized iCal bytes safe for parsing
    """
    original_len = len(ics_bytes)
    sanitized = ics_bytes

    # Remove bogus DTEND lines (e.g., "DTEND:-47120101T235959")
    # These break date parsing - better to have no DTEND than an invalid one
    sanitized = _BOGUS_DTEND_RE.sub(b"", sanitized)

    # Remove empty UNTIL= from RRULE (e.g., "UNTIL=;" -> "")
    # An empty UNTIL means "forever" - just omit it entirely
    sanitized = _EMPTY_UNTIL_RE.sub(b"", sanitized)

    if len(sanitized) != original_len:
        logger.debug(
            "Sanitized malformed Popmenu iCal data",
            extra={
                "original_bytes": original_len,
                "sanitized_bytes": len(sanitized),
                "bytes_removed": original_len - len(sanitized),
            },
        )

    return sanitized


DEFAULT_TZ = ZoneInfo("America/New_York")

# How far into the future to expand recurring events (6 months)
DEFAULT_EXPAND_MONTHS = 6

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/calendar,text/plain;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


@dataclass(frozen=True)
class ParsedICalEvent:
    uid: str
    summary: str
    description: str | None
    location: str | None
    start_utc: datetime
    end_utc: datetime | None
    url: str | None
    categories: list[str]


def _normalize_categories(value: Any) -> list[str]:
    if value is None:
        return []

    raw_items: list[str]
    if hasattr(value, "cats"):
        raw_items = [str(item) for item in value.cats]
    elif isinstance(value, list | tuple | set):
        raw_items = [str(item) for item in value]
    else:
        raw_items = [str(item) for item in str(value).split(",")]

    seen: set[str] = set()
    categories: list[str] = []
    for item in raw_items:
        cleaned = item.strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        categories.append(cleaned)

    return categories


# ---------------------------------------------------------------------------
# Cloudflare challenge detection
# ---------------------------------------------------------------------------


class CloudflareChallengeError(Exception):
    """Raised when Cloudflare serves a challenge page instead of iCal data."""


def _is_cloudflare_challenge(resp: requests.Response) -> bool:
    """Return *True* if *resp* looks like a Cloudflare challenge page."""
    # CF challenges that come back as non-200 (403, 503)
    if resp.headers.get("cf-mitigated") == "challenge":
        return True

    content_type = resp.headers.get("Content-Type", "")
    if "text/html" not in content_type:
        return False

    body = resp.text[:2000].lower()
    cf_signals = [
        "cloudflare",
        "cf-browser-verification",
        "challenge-platform",
        "just a moment",
        "cf_chl_opt",
        "cf-ray",
    ]
    return any(signal in body for signal in cf_signals)


def _validate_ical_content(content: bytes) -> bool:
    """Return *True* if *content* looks like valid iCal data."""
    stripped = content.lstrip(b"\xef\xbb\xbf").strip()
    return stripped.startswith(b"BEGIN:VCALENDAR")


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------


def create_ical_session() -> requests.Session:
    """Create an HTTP session configured for iCal fetching.

    Returns a :class:`requests.Session` with browser-like headers.
    Re-using a single session across multiple :func:`fetch_ics` calls
    preserves cookies (including Cloudflare ``__cf_bm`` / ``cf_clearance``)
    and lowers the chance of being challenged.
    """
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def warm_session(session: requests.Session, ical_url: str) -> None:
    """Visit the base domain to pre-establish Cloudflare cookies.

    Call this once before a batch of :func:`fetch_ics` calls that target
    the same domain.  The GET to the root page picks up ``__cf_bm`` /
    ``cf_clearance`` cookies that subsequent ``.ics`` requests can reuse.
    """
    parsed = urlparse(ical_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    try:
        logger.debug("Warming session", extra={"base_url": base_url})
        resp = session.get(base_url, timeout=15)
        logger.debug(
            "Session warmed",
            extra={
                "base_url": base_url,
                "status_code": resp.status_code,
                "cookies": list(session.cookies.keys()),
            },
        )
    except requests.RequestException as e:
        logger.debug(
            "Session warmup failed (non-fatal)",
            extra={"base_url": base_url, "error": str(e)},
        )


# ---------------------------------------------------------------------------
# iCal fetching
# ---------------------------------------------------------------------------


def fetch_ics(
    url: str,
    *,
    session: requests.Session | None = None,
    max_retries: int = 3,
    base_delay: float = 2.0,
) -> bytes:
    """Fetch iCal data from a URL.

    Includes Cloudflare challenge detection and retry with exponential
    backoff.  When a challenge page is detected instead of iCal data the
    request is retried up to *max_retries* times with increasing delays
    (``base_delay * 2^attempt``, plus jitter).

    Args:
        url: The iCal URL to fetch.
        session: Optional :class:`requests.Session` to reuse for cookie
            persistence across multiple fetches.  If *None* a throwaway
            session is created (old behaviour).
        max_retries: Maximum number of retries on Cloudflare challenges.
        base_delay: Base delay in seconds for exponential backoff.

    Returns:
        Raw iCal bytes.

    Raises:
        CloudflareChallengeError: If all retries are exhausted due to
            Cloudflare challenges.
        ValueError: If the response is not valid iCal data (and is not a
            recognisable Cloudflare page either).
        requests.RequestException: For non-Cloudflare HTTP errors.
    """
    s = session or create_ical_session()
    logger.debug("Fetching iCal data", extra={"url": url})

    last_cf_error: CloudflareChallengeError | None = None

    for attempt in range(1 + max_retries):
        try:
            resp = s.get(url, timeout=25, allow_redirects=True)

            # --- Cloudflare challenge (may be 200, 403, or 503) ----------
            if _is_cloudflare_challenge(resp):
                delay = base_delay * (2**attempt) + random.uniform(0, 1)
                last_cf_error = CloudflareChallengeError(
                    f"Cloudflare challenge on attempt {attempt + 1} for {url}"
                )
                logger.warning(
                    "Cloudflare challenge detected",
                    extra={
                        "url": url,
                        "attempt": attempt + 1,
                        "max_attempts": 1 + max_retries,
                        "status_code": resp.status_code,
                        "retry_delay": round(delay, 1),
                        "cf_ray": resp.headers.get("cf-ray"),
                    },
                )
                if attempt < max_retries:
                    time.sleep(delay)
                    continue
                raise last_cf_error

            resp.raise_for_status()

            # --- Content validation --------------------------------------
            if not _validate_ical_content(resp.content):
                logger.warning(
                    "Response is not valid iCal data",
                    extra={
                        "url": url,
                        "content_type": resp.headers.get("Content-Type"),
                        "content_preview": resp.content[:200].decode(
                            "utf-8", errors="replace"
                        ),
                    },
                )
                raise ValueError(
                    f"Expected iCal data but got unexpected content from {url}"
                )

            logger.debug(
                "Successfully fetched iCal data",
                extra={"url": url, "content_length": len(resp.content)},
            )
            return resp.content

        except (CloudflareChallengeError, ValueError):
            raise
        except requests.RequestException as e:
            # A non-200 response that is also a CF challenge
            if (
                hasattr(e, "response")
                and e.response is not None
                and _is_cloudflare_challenge(e.response)
            ):
                delay = base_delay * (2**attempt) + random.uniform(0, 1)
                last_cf_error = CloudflareChallengeError(
                    f"Cloudflare challenge (HTTP {e.response.status_code}) "
                    f"on attempt {attempt + 1} for {url}"
                )
                logger.warning(
                    "Cloudflare challenge detected (HTTP error)",
                    extra={
                        "url": url,
                        "attempt": attempt + 1,
                        "max_attempts": 1 + max_retries,
                        "status_code": e.response.status_code,
                        "retry_delay": round(delay, 1),
                    },
                )
                if attempt < max_retries:
                    time.sleep(delay)
                    continue
                raise last_cf_error from e

            # Genuine HTTP error – don't retry
            logger.error(
                "Failed to fetch iCal data",
                extra={"url": url, "error_type": type(e).__name__},
                exc_info=True,
            )
            raise

    # Should not be reached, but satisfies the type checker
    raise last_cf_error or RuntimeError(f"Failed to fetch {url}")


def _dt_to_utc(value: Any, *, default_tz: ZoneInfo) -> datetime:
    """
    Handles:
    - date (all-day) -> midnight local -> UTC
    - datetime naive -> assume default_tz -> UTC
    - datetime aware -> convert -> UTC
    """
    if value is None:
        raise ValueError("Missing DTSTART/DTEND")

    # date-only all-day
    if hasattr(value, "year") and not hasattr(value, "hour"):
        local = datetime.combine(value, dt_time(0, 0), tzinfo=default_tz)
        return local.astimezone(UTC)

    dt: datetime = value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=default_tz)
    return dt.astimezone(UTC)


def parse_ics(
    ics_bytes: bytes,
    *,
    default_tz: ZoneInfo = DEFAULT_TZ,
    expand_months: int = DEFAULT_EXPAND_MONTHS,
) -> list[ParsedICalEvent]:
    """
    Parse iCal bytes into a list of events.

    Expands recurring events (RRULE, RDATE) into individual occurrences
    within the date range from now to `expand_months` in the future.

    Note: Input is sanitized to fix known issues with Popmenu's iCal export
    (malformed DTEND dates and empty UNTIL parameters in RRULEs).
    """
    logger.debug(
        "Parsing iCal data",
        extra={"bytes_length": len(ics_bytes), "expand_months": expand_months},
    )
    try:
        # Sanitize malformed iCal data (fixes Popmenu/Big Top recurring events)
        ics_bytes = _sanitize_popmenu_ical(ics_bytes)

        cal = Calendar.from_ical(ics_bytes)
        out: list[ParsedICalEvent] = []

        # Define the date range for expanding recurring events
        now = datetime.now(UTC)
        start_range = now - timedelta(days=1)  # Include events starting yesterday
        end_range = now + timedelta(days=expand_months * 30)

        # Use recurring_ical_events to expand recurring events
        # This handles RRULE, RDATE, EXDATE, etc.
        expanded_events = recurring_ical_events.of(cal).between(start_range, end_range)

        for comp in expanded_events:
            uid = str(comp.get("UID") or "").strip()
            if not uid:
                logger.debug("Skipping event without UID")
                continue

            summary = str(comp.get("SUMMARY") or "").strip() or "(Untitled)"
            description = str(comp.get("DESCRIPTION") or "").strip() or None
            location = str(comp.get("LOCATION") or "").strip() or None
            categories = _normalize_categories(comp.get("CATEGORIES"))

            dtstart = comp.get("DTSTART")
            dtend = comp.get("DTEND")

            try:
                start_utc = _dt_to_utc(
                    dtstart.dt if dtstart else None, default_tz=default_tz
                )

                end_utc = None
                if dtend is not None:
                    end_utc = _dt_to_utc(dtend.dt, default_tz=default_tz)

                # Some feeds include a URL per event
                url = str(comp.get("URL") or "").strip() or None

                out.append(
                    ParsedICalEvent(
                        uid=uid,
                        summary=summary,
                        description=description,
                        location=location,
                        start_utc=start_utc,
                        end_utc=end_utc,
                        url=url,
                        categories=categories,
                    )
                )
            except (ValueError, AttributeError) as e:
                logger.warning(
                    "Error parsing event dates",
                    extra={"uid": uid, "error_type": type(e).__name__},
                    exc_info=True,
                )
                continue

        logger.info(
            "Successfully parsed iCal data",
            extra={
                "events_parsed": len(out),
                "default_tz": str(default_tz),
                "expand_months": expand_months,
            },
        )
        return out
    except Exception as e:
        logger.error(
            "Failed to parse iCal data",
            extra={"error_type": type(e).__name__},
            exc_info=True,
        )
        raise
