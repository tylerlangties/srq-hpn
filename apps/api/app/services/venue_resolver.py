from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.venue import Venue
from app.models.venue_alias import VenueAlias

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]")  # keep letters/numbers/underscore + whitespace


def normalize_location(text: str) -> str:
    text = text.strip().lower()
    text = _PUNCT.sub(" ", text)
    text = _WS.sub(" ", text)
    return text.strip()


def resolve_venue_id(db: Session, location_text: str | None) -> int | None:
    """
    Layer 1 deterministic matching:
      1) venue_aliases.alias_normalized exact match
      2) exact normalized match against venues.name
    """
    if not location_text or not location_text.strip():
        return None

    norm = normalize_location(location_text)

    alias = db.scalar(select(VenueAlias).where(VenueAlias.alias_normalized == norm))
    if alias:
        return alias.venue_id

    # exact normalized match on venue name
    venues = db.execute(select(Venue.id, Venue.name)).all()
    for vid, vname in venues:
        if normalize_location(vname) == norm:
            return vid

    return None
