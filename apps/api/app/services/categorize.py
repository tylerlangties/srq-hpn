"""
Event categorization service.

Provides:
- A static registry of categories with keyword patterns for inference
- Keyword-based category inference from event title / description
- Shared DB helpers for get-or-create and idempotent attachment

Both iCal (feed) and direct (HTML/API) collectors converge at
``upsert_event_and_occurrence``, which calls into this module so that
*every* ingested event is automatically categorised.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from typing import Final

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.event_category import EventCategory

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Slug helper
# ---------------------------------------------------------------------------

_SLUG_RE: Final = re.compile(r"[^a-z0-9]+")


def _slugify(value: str) -> str:
    return _SLUG_RE.sub("-", value.strip().lower()).strip("-")


# ---------------------------------------------------------------------------
# Category keyword registry
# ---------------------------------------------------------------------------
# Maps a human-readable category name to a list of keyword / phrase strings.
# At module-load time these are compiled into word-boundary regexes so that
# ``infer_categories`` is fast on every call.
#
# To add a new category, just add an entry here – no migration needed (the
# categories table is populated on-demand via get_or_create).
# ---------------------------------------------------------------------------

CATEGORY_KEYWORDS: Final[dict[str, list[str]]] = {
    "Performing Arts": [
        "theater",
        "theatre",
        "broadway",
        "opera",
        "ballet",
        "symphony",
        "orchestra",
        "playhouse",
        "musical",
        "performing art",
        "stage show",
        "repertory",
        "cabaret",
        "recital",
        "dance performance",
        "one-man show",
        "one-woman show",
    ],
    "Live Music": [
        "concert",
        "live music",
        "acoustic",
        "jazz",
        "blues",
        "rock",
        "country music",
        "folk music",
        "singer-songwriter",
        "open mic",
        "jam session",
        "ensemble",
        "choir",
        "choral",
    ],
    "Visual Arts": [
        "art exhibit",
        "art show",
        "art gallery",
        "exhibition",
        "painting",
        "sculpture",
        "photography exhibit",
        "art festival",
        "art walk",
        "ceramics",
        "watercolor",
        "mixed media",
        "printmaking",
        "glass art",
        "art fair",
    ],
    "Family & Kids": [
        "kids",
        "children",
        "family friendly",
        "family-friendly",
        "youth",
        "camp",
        "storytime",
        "story time",
        "toddler",
        "all ages",
        "puppet",
        "face paint",
    ],
    "Food & Drink": [
        "food truck",
        "food fest",
        "wine tasting",
        "beer tasting",
        "brewery",
        "tasting",
        "brunch",
        "culinary",
        "chef",
        "cocktail",
        "distillery",
        "farm to table",
        "food festival",
    ],
    "Outdoors & Nature": [
        "garden tour",
        "hike",
        "hiking",
        "kayak",
        "wildlife",
        "birding",
        "bird walk",
        "nature walk",
        "eco tour",
        "conservation",
        "paddleboard",
        "snorkel",
        "fishing",
        "botanical",
        "nature preserve",
    ],
    "Sports & Fitness": [
        "fitness",
        "marathon",
        "yoga",
        "5k",
        "10k",
        "triathlon",
        "cycling",
        "golf tournament",
        "tennis",
        "pickleball",
        "regatta",
        "sailing",
        "fun run",
    ],
    "Comedy": [
        "comedy",
        "comedian",
        "standup",
        "stand-up",
        "improv",
        "sketch comedy",
        "comedy show",
        "comedy night",
    ],
    "Festivals & Fairs": [
        "festival",
        "fair",
        "parade",
        "carnival",
        "block party",
        "street fair",
        "fiesta",
        "jubilee",
    ],
    "Education & Workshops": [
        "workshop",
        "lecture",
        "seminar",
        "masterclass",
        "certification",
        "panel discussion",
        "webinar",
    ],
    "Community": [
        "volunteer",
        "fundraiser",
        "charity",
        "benefit gala",
        "nonprofit",
        "gala",
        "auction",
        "networking event",
    ],
    "Markets & Shopping": [
        "farmers market",
        "flea market",
        "craft fair",
        "artisan market",
        "pop-up shop",
        "antique",
        "bazaar",
    ],
    "Film & Cinema": [
        "film screening",
        "movie night",
        "cinema",
        "documentary",
        "film festival",
        "short film",
    ],
    "Holiday & Seasonal": [
        "christmas",
        "halloween",
        "new year",
        "easter",
        "thanksgiving",
        "memorial day",
        "independence day",
        "fourth of july",
        "valentines",
        "mardi gras",
        "holiday",
    ],
    "Nightlife": [
        "dj",
        "dance party",
        "club night",
        "happy hour",
        "karaoke",
        "late night",
    ],
}


# ---------------------------------------------------------------------------
# Compiled patterns  (built once at import time)
# ---------------------------------------------------------------------------


def _compile_keywords(
    registry: dict[str, list[str]],
) -> dict[str, re.Pattern[str]]:
    """Compile each category's keyword list into a single OR-ed regex."""
    compiled: dict[str, re.Pattern[str]] = {}
    for category_name, keywords in registry.items():
        # Escape each keyword, then join with ``|``
        escaped = [re.escape(kw) for kw in keywords]
        pattern = r"\b(?:" + "|".join(escaped) + r")\b"
        compiled[category_name] = re.compile(pattern, re.IGNORECASE)
    return compiled


_COMPILED_PATTERNS: Final = _compile_keywords(CATEGORY_KEYWORDS)

# Lookup table: lowercased name → canonical name for fast membership checks.
_KNOWN_CATEGORIES_LOWER: Final[dict[str, str]] = {
    name.lower(): name for name in CATEGORY_KEYWORDS
}


# ---------------------------------------------------------------------------
# Public API – filtering
# ---------------------------------------------------------------------------


def filter_known_categories(names: Iterable[str]) -> list[str]:
    """
    Return only category names that match a known category (case-insensitive).

    Unknown names (e.g. garbage from iCal CATEGORIES fields) are silently
    dropped.  Matching names are normalised to their canonical spelling.
    """
    result: list[str] = []
    for name in names:
        canonical = _KNOWN_CATEGORIES_LOWER.get(name.strip().lower())
        if canonical:
            result.append(canonical)
    return result


# ---------------------------------------------------------------------------
# Public API – inference
# ---------------------------------------------------------------------------


def infer_categories(
    title: str | None,
    description: str | None,
) -> set[str]:
    """
    Return the set of category *names* whose keywords appear in *title*
    or *description*.

    Fast: each category is a single compiled regex scan over the combined
    text.
    """
    text = " ".join(part for part in (title, description) if part)
    if not text:
        return set()

    matched: set[str] = set()
    for category_name, pattern in _COMPILED_PATTERNS.items():
        if pattern.search(text):
            matched.add(category_name)
    return matched


# ---------------------------------------------------------------------------
# Public API – database helpers
# ---------------------------------------------------------------------------


def get_or_create_category(db: Session, name: str) -> Category:
    """Return an existing ``Category`` or create one on the fly."""
    existing = db.scalar(select(Category).where(Category.name == name))
    if existing:
        return existing

    category = Category(name=name, slug=_slugify(name))
    db.add(category)
    db.flush()
    return category


def attach_category(db: Session, *, event_id: int, category_id: int) -> None:
    """Idempotently link an event to a category (ON CONFLICT DO NOTHING)."""
    stmt = (
        insert(EventCategory)
        .values(event_id=event_id, category_id=category_id)
        .on_conflict_do_nothing(constraint="uq_event_category")
    )
    db.execute(stmt)


def apply_categories(
    db: Session,
    event_id: int,
    category_names: Iterable[str],
) -> None:
    """
    Resolve each category name to a ``Category`` row and attach it to the
    event.  Safe to call repeatedly – duplicate links are silently ignored.
    """
    for name in category_names:
        name = name.strip()
        if not name:
            continue
        cat = get_or_create_category(db, name)
        attach_category(db, event_id=event_id, category_id=cat.id)
