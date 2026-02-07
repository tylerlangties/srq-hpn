"""
Event Collectors

This package contains collectors that fetch event data from external sources.

There are two kinds of collectors:

1. **Feed collectors** — discover iCal feed URLs and store them in the
   ``source_feeds`` table for later ingestion (bigtop, mote, mustdo, selby).
2. **Direct collectors** — scrape event data and write events +
   event_occurrences straight to the database (artfestival, asolorep,
   bigwaters, sarasotafair, vanwezel).

Every collector exposes a ``run_collector(db, source, *, ...)`` function that
can be called from Celery tasks or the CLI, and a ``main()`` entry point for
``python -m app.collectors.<name> --source-id <id>`` usage.

Shared utilities live in ``collectors.utils``.
"""
