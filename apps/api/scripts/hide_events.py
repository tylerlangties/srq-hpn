"""
Bulk-hide (or unhide) events by event IDs or by source + external_ids.

Use after ingestion to hide mustdo events that are "not local enough".
Hidden events are excluded from the public /api/events/* endpoints and stay
hidden across re-ingestion.

Examples (run from apps/api so "app" is importable):

  # Hide events by external_id (e.g. iCal UIDs), one per line in a file:
  python scripts/hide_events.py --source mustdo --external-ids-file ids.txt

  # Hide by event IDs (from DB or admin list):
  python scripts/hide_events.py --event-ids-file event_ids.txt

  # Unhide (set hidden=False):
  python scripts/hide_events.py --source mustdo --external-ids-file ids.txt --show

  # Dry run:
  python scripts/hide_events.py --source mustdo --external-ids-file ids.txt --dry-run
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from sqlalchemy import select

import app.core.env  # noqa: F401
from app.core.logging import setup_logging
from app.db import SessionLocal
from app.models.event import Event
from app.models.source import Source

logger = logging.getLogger(__name__)


def _read_lines(path: Path) -> list[str]:
    with path.open() as f:
        return [line.strip() for line in f if line.strip()]


def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Bulk set hidden on events by event IDs or (source + external_ids)"
    )
    parser.add_argument(
        "--source",
        type=str,
        help="Source name (e.g. 'mustdo') when using --external-ids-file",
    )
    parser.add_argument(
        "--external-ids-file",
        type=Path,
        metavar="FILE",
        help="File with one event external_id (e.g. iCal UID) per line; requires --source",
    )
    parser.add_argument(
        "--event-ids-file",
        type=Path,
        metavar="FILE",
        help="File with one event ID per line",
    )
    parser.add_argument(
        "--hidden",
        dest="hidden",
        action="store_true",
        default=True,
        help="Set hidden=True (default)",
    )
    parser.add_argument(
        "--show",
        dest="hidden",
        action="store_false",
        help="Set hidden=False (unhide)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write to DB, only report what would be updated",
    )
    args = parser.parse_args()

    if args.event_ids_file is not None:
        ids = _read_lines(args.event_ids_file)
        try:
            event_ids = [int(x) for x in ids]
        except ValueError as e:
            logger.error("All lines in --event-ids-file must be integers: %s", e)
            sys.exit(1)
        source_name = None
        external_ids = None
    elif args.external_ids_file is not None and args.source:
        external_ids = _read_lines(args.external_ids_file)
        event_ids = None
        source_name = args.source
    else:
        logger.error(
            "Use either --event-ids-file or (--source and --external-ids-file)"
        )
        sys.exit(1)

    db = SessionLocal()
    try:
        if event_ids is not None:
            stmt = select(Event).where(Event.id.in_(event_ids))
            events = list(db.scalars(stmt).all())
            missing = set(event_ids) - {e.id for e in events}
            if missing:
                logger.warning("Event IDs not found: %s", sorted(missing))
        else:
            source = db.scalar(select(Source).where(Source.name == source_name))
            if source is None:
                logger.error("Source not found: %s", source_name)
                sys.exit(1)
            stmt = select(Event).where(
                Event.source_id == source.id,
                Event.external_id.in_(external_ids),
            )
            events = list(db.scalars(stmt).all())
            seen = {e.external_id for e in events}
            missing = [x for x in external_ids if x not in seen]
            if missing:
                logger.warning(
                    "External IDs not found (first 10): %s",
                    missing[:10],
                )

        to_change = [e for e in events if e.hidden != args.hidden]
        if not to_change:
            logger.info(
                "No events to update (all %d already have hidden=%s)",
                len(events),
                args.hidden,
            )
            return

        if args.dry_run:
            logger.info(
                "DRY RUN: would set hidden=%s on %d events (of %d in file)",
                args.hidden,
                len(to_change),
                len(events),
            )
            for e in to_change[:5]:
                logger.info(
                    "  event_id=%s external_id=%s title=%s",
                    e.id,
                    e.external_id,
                    (e.title or "")[:50],
                )
            if len(to_change) > 5:
                logger.info("  ... and %d more", len(to_change) - 5)
            return

        for e in to_change:
            e.hidden = args.hidden
        db.commit()
        logger.info(
            "Set hidden=%s on %d events",
            args.hidden,
            len(to_change),
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
