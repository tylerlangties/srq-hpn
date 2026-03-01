from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Final

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.event_occurrence import EventOccurrence
from app.models.source import Source
from app.services.categorize import (
    apply_categories,
    filter_known_categories,
    infer_categories,
)
from app.services.venue_resolver import resolve_venue_id

DEFAULT_TIMEZONE: Final[str] = "America/New_York"

NUMBER_RE = re.compile(r"\b\d{1,6}\b")
STREET_SUFFIX_RE = re.compile(
    r"\b(St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Dr|Drive|Ln|Lane|Ct|Court|Cir|"
    r"Circle|Hwy|Highway|Pkwy|Parkway|Way|Pl|Place|Ter|Terrace)\b",
    re.IGNORECASE,
)
COUNTRY_SEGMENTS = {"united states", "usa", "us"}


def slugify(value: str) -> str:
    import re

    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def _truncate(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return value[:max_len].rstrip("-")


def _normalize_location(location: str) -> str:
    return " ".join(location.replace("\n", " ").replace("\r", " ").split())


def _extract_address(location: str | None) -> str | None:
    if not location:
        return None
    normalized = _normalize_location(location)
    segments = [seg.strip() for seg in normalized.split(",") if seg.strip()]
    if not segments:
        return None

    start_idx = None
    for idx, seg in enumerate(segments):
        if NUMBER_RE.search(seg) and STREET_SUFFIX_RE.search(seg):
            start_idx = idx
            break

    if start_idx is None:
        return None

    address_parts: list[str] = []
    for seg in segments[start_idx:]:
        if seg.lower() in COUNTRY_SEGMENTS:
            break
        address_parts.append(seg)

    if not address_parts:
        return None

    return ", ".join(address_parts)


def _build_event_slug(*, title: str, source_id: int, external_id: str) -> str:
    base = slugify(title) or "event"

    frag = external_id.split("@", 1)[0]
    frag = slugify(frag) or "ext"
    frag = _truncate(frag, 24)

    slug = f"{base}-{source_id}-{frag}"
    return _truncate(slug, 120)


def _get_event(db: Session, *, source_id: int, external_id: str) -> Event | None:
    return db.scalar(
        select(Event).where(
            Event.source_id == source_id, Event.external_id == external_id
        )
    )


def _get_occurrence(
    db: Session, *, event_id: int, start_utc: datetime
) -> EventOccurrence | None:
    return db.scalar(
        select(EventOccurrence).where(
            EventOccurrence.event_id == event_id,
            EventOccurrence.start_datetime_utc == start_utc,
        )
    )


def _normalize_title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def _get_event_by_semantic_key(
    db: Session, *, source_id: int, title: str, start_utc: datetime
) -> Event | None:
    title_key = _normalize_title_key(title)
    if not title_key:
        return None

    title_expr = func.regexp_replace(func.lower(Event.title), r"[^a-z0-9]+", " ", "g")
    return db.scalar(
        select(Event)
        .join(EventOccurrence, EventOccurrence.event_id == Event.id)
        .where(
            Event.source_id == source_id,
            EventOccurrence.start_datetime_utc == start_utc,
            title_expr == title_key,
        )
        .order_by(Event.id.asc())
        .limit(1)
    )


def upsert_event_and_occurrence(
    db: Session,
    *,
    source: Source,
    external_id: str,
    title: str,
    description: str | None,
    location: str | None,
    start_utc: datetime,
    end_utc: datetime | None,
    external_url: str | None,
    fallback_external_url: str | None,
    categories: list[str] | None = None,
) -> Event:
    """
    Generic event upsert:
      - Events dedupe: unique(source_id, external_id)
        * external_id should be the iCal event UID (from VEVENT.UID)
        * This is different from SourceFeed.external_id (which identifies the iCal file)
      - Occurrences dedupe: unique(event_id, start_datetime_utc)

    Stores raw LOCATION into EventOccurrence.location_text.
    Attempts deterministic venue match -> EventOccurrence.venue_id.

    Categories are applied from three sources (all merged, all idempotent):
      1. *categories* – explicit names passed by the caller
      2. ``source.default_categories`` – blanket categories for this source
      3. Keyword inference on *title* / *description*
    """

    if start_utc.tzinfo is None:
        raise ValueError("start_utc must be timezone-aware (UTC)")

    if end_utc is not None and end_utc.tzinfo is None:
        raise ValueError("end_utc must be timezone-aware (UTC)")

    if end_utc is not None and end_utc < start_utc:
        end_utc = None

    final_url = external_url or fallback_external_url
    now = datetime.now(UTC)

    # ---- Event upsert (airtight with uniqueness constraint) ----
    event = _get_event(db, source_id=source.id, external_id=external_id)
    if event is None:
        event = _get_event_by_semantic_key(
            db,
            source_id=source.id,
            title=title,
            start_utc=start_utc,
        )

    if event is None:
        slug = _build_event_slug(
            title=title, source_id=source.id, external_id=external_id
        )

        event = Event(
            title=title,
            description=description,
            slug=slug,
            is_free=False,  # unknown from iCal
            price_text=None,
            status="scheduled",
            source_id=source.id,
            external_id=external_id,
            external_url=final_url,
            last_seen_at=now,
            venue_id=None,  # important: venue is now on occurrences
        )
        db.add(event)

        try:
            db.flush()  # may raise if another process inserted same (source_id, external_id)
        except IntegrityError:
            db.rollback()
            event = _get_event(db, source_id=source.id, external_id=external_id)
            if event is None:
                raise
    else:
        event.title = title
        event.description = description
        if event.external_id is None:
            event.external_id = external_id
        event.external_url = final_url
        event.last_seen_at = now

    # ---- Occurrence upsert (airtight with uniqueness constraint) ----
    resolved_venue_id = resolve_venue_id(db, location)
    address_text = _extract_address(location)
    occ = _get_occurrence(db, event_id=event.id, start_utc=start_utc)

    if occ is None:
        occ = EventOccurrence(
            event_id=event.id,
            start_datetime_utc=start_utc,
            end_datetime_utc=end_utc,
            location_text=location,
            address_text=address_text,
            venue_id=resolved_venue_id,
        )
        db.add(occ)

        try:
            db.flush()  # may raise if another process inserted same (event_id, start_datetime_utc)
        except IntegrityError:
            db.rollback()
            occ = _get_occurrence(db, event_id=event.id, start_utc=start_utc)
            if occ is None:
                raise
            # If it already existed, update it (safe idempotency)
            occ.end_datetime_utc = end_utc
            occ.location_text = location
            occ.address_text = address_text
            occ.venue_id = resolved_venue_id
    else:
        occ.end_datetime_utc = end_utc
        occ.location_text = location
        occ.address_text = address_text
        occ.venue_id = resolved_venue_id

    # ---- Category assignment (idempotent – safe to call on every occurrence) ----
    all_categories: set[str] = set()

    # 1. Explicit categories from the caller (filtered to known registry)
    if categories:
        all_categories.update(filter_known_categories(categories))

    # 2. Blanket categories from the source (filtered to known registry)
    if source.default_categories:
        all_categories.update(
            filter_known_categories(
                cat.strip()
                for cat in source.default_categories.split(",")
                if cat.strip()
            )
        )

    # 3. Keyword-inferred categories from title + description
    all_categories.update(infer_categories(title, description))

    if all_categories:
        apply_categories(db, event.id, all_categories)

    return event
