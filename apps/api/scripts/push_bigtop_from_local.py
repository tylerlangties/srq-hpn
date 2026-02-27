from __future__ import annotations

import argparse
import logging
import os
from typing import Any

import app.core.env  # noqa: F401
from app.collectors.bigtop import DEFAULT_CREATED_MONTHS, run_collector
from app.core.logging import setup_logging
from app.db import SessionLocal
from app.models.source import Source
from app.services.ingest_sink import DbSink, MultiSink, ProdApiSink
from app.services.ingest_source_items import ingest_source_items

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
DEFAULT_BATCH_SIZE = 250


def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Run Big Top collector+ingester locally and optionally push to prod"
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
    parser.add_argument(
        "--push-prod",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--source-id", type=int, default=5)
    parser.add_argument("--limit", type=int, default=500)
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
        help="Comma-separated categories to attach to source feeds",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.push_prod and not args.api_base:
        raise SystemExit("--api-base (or BIGTOP_INGEST_API_BASE) is required")
    if args.push_prod and not args.token:
        raise SystemExit("--token (or BIGTOP_INGEST_TOKEN) is required")
    if args.batch_size < 1 or args.batch_size > 500:
        raise SystemExit("--batch-size must be between 1 and 500")
    if args.limit < 1:
        raise SystemExit("--limit must be at least 1")

    db = SessionLocal()
    try:
        source = db.get(Source, args.source_id)
        if source is None:
            raise SystemExit(f"Source {args.source_id} not found in local DB")

        categories = [
            c.strip() for c in (args.categories or "").split(",") if c.strip()
        ]
        categories_arg = ",".join(categories) if categories else None

        logger.info(
            "Starting local Big Top sync (collector + ingester)",
            extra={
                "source_id": args.source_id,
                "future_only": args.future_only,
                "created_months": args.created_months,
                "limit": args.limit,
                "push_prod": args.push_prod,
                "dry_run": args.dry_run,
            },
        )

        collector_stats = run_collector(
            db,
            source,
            delay=args.delay,
            future_only=args.future_only,
            created_months=args.created_months,
            categories=categories_arg,
            dry_run=args.dry_run,
        )

        sink: DbSink | MultiSink = DbSink()
        prod_sink: ProdApiSink | None = None

        # Local DB writes always happen in ingest_source_items; this fan-out adds prod push.
        if args.push_prod and not args.dry_run:
            prod_sink = ProdApiSink(
                api_base=args.api_base,
                token=args.token,
                batch_size=args.batch_size,
                timeout_seconds=args.timeout,
                retries=args.retries,
            )
            sink = MultiSink([DbSink(), prod_sink])

        ingest_stats = ingest_source_items(
            db,
            source=source,
            limit=args.limit,
            delay=args.delay,
            sink=sink,
        )
        db.commit()

        summary: dict[str, Any] = {
            "collector": collector_stats,
            "ingest": ingest_stats,
            "prod_push": {
                "enabled": bool(prod_sink),
                "run_id": prod_sink.run_id if prod_sink else None,
                "received": prod_sink.received if prod_sink else 0,
                "upserted": prod_sink.upserted if prod_sink else 0,
                "rejected": prod_sink.rejected if prod_sink else 0,
            },
        }
        logger.info("Local Big Top sync completed", extra=summary)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
