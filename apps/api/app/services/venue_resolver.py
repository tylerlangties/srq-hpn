from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.venue import Venue
from app.models.venue_alias import VenueAlias

logger = logging.getLogger(__name__)

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]")  # keep letters/numbers/underscore + whitespace

# Conservative threshold for fuzzy matching (85% similarity)
FUZZY_MATCH_THRESHOLD = 0.85


def normalize_location(text: str) -> str:
    text = text.strip().lower()
    text = _PUNCT.sub(" ", text)
    text = _WS.sub(" ", text)
    return text.strip()


def _similarity_ratio(a: str, b: str) -> float:
    """Calculate similarity ratio between two strings using SequenceMatcher."""
    return SequenceMatcher(None, a, b).ratio()


def resolve_venue_id(db: Session, location_text: str | None) -> int | None:
    """
    Multi-layer venue resolution:
    Layer 1 (deterministic):
      1) venue_aliases.alias_normalized exact match
      2) exact normalized match against venues.name
    Layer 2 (fuzzy):
      3) fuzzy match against venue aliases (if Layer 1 fails)
      4) fuzzy match against venue names (if Layer 1 fails)

    Returns venue_id if confident match found, None otherwise.
    """
    if not location_text or not location_text.strip():
        return None

    norm = normalize_location(location_text)

    # Layer 1: Deterministic matching
    alias = db.scalar(select(VenueAlias).where(VenueAlias.alias_normalized == norm))
    if alias:
        return alias.venue_id

    # exact normalized match on venue name
    venues = db.execute(select(Venue.id, Venue.name)).all()
    for vid, vname in venues:
        if normalize_location(vname) == norm:
            return vid

    # Layer 2: Fuzzy matching (only if deterministic matching failed)
    best_match_id: int | None = None
    best_ratio = 0.0

    # Fuzzy match against aliases
    aliases = db.execute(select(VenueAlias.venue_id, VenueAlias.alias_normalized)).all()
    for venue_id, alias_norm in aliases:
        ratio = _similarity_ratio(norm, alias_norm)
        if ratio > best_ratio and ratio >= FUZZY_MATCH_THRESHOLD:
            best_ratio = ratio
            best_match_id = venue_id

    # Fuzzy match against venue names
    for vid, vname in venues:
        vname_norm = normalize_location(vname)
        ratio = _similarity_ratio(norm, vname_norm)
        if ratio > best_ratio and ratio >= FUZZY_MATCH_THRESHOLD:
            best_ratio = ratio
            best_match_id = vid

    if best_match_id is not None:
        logger.info(
            "Fuzzy venue match",
            extra={
                "location_text": location_text,
                "venue_id": best_match_id,
                "similarity": f"{best_ratio:.2f}",
            },
        )
        return best_match_id

    return None
