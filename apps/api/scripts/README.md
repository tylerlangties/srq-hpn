# Collector CLI Contract

All collectors accept these shared CLI args:

- `--source-id` (required): source id from the database.
- `--dry-run`: simulate writes without persisting to the database.
- `--delay`: delay between requests.
- `--max-pages`: pagination cap when applicable; accepted as a no-op for collectors that do not paginate by pages.
- `--validate-ical`: validate discovered iCal URLs where applicable; accepted as a no-op otherwise.
- `--future-only`: include only future events where applicable; accepted as a no-op otherwise.
- `--categories`: comma-separated categories to attach to source feeds where applicable; accepted as a no-op otherwise.

Collector-specific flags may still exist (examples: `--months-ahead`, `--filters`, `--created-months`, `--max-days`, `--chunk-size`).

## Current Collector Notes

- `app.collectors.selby`: full shared contract plus `--filters`, `--published-months`, `--list-categories`.
- `app.collectors.bigtop`: full shared contract; `--max-pages` accepted as a no-op.
- `app.collectors.mote`: full shared contract; `--max-pages` and `--future-only` accepted as no-ops.
- `app.collectors.mustdo` (deprecated): full shared contract; `--future-only` accepted as a no-op.
- `app.collectors.vanwezel`: full shared contract; feed-oriented flags accepted as no-ops.
- `app.collectors.artfestival`: full shared contract; feed-oriented flags accepted as no-ops.
- `app.collectors.asolorep`: full shared contract; `--validate-ical` and `--categories` accepted as no-ops.
- `app.collectors.bigwaters`: full shared contract; supports both `--future-only` and legacy `--include-past`.
- `app.collectors.sarasotafair`: full shared contract; `--max-pages` and feed-oriented flags accepted as no-ops.

## Example

Run any collector from `apps/api`:

```bash
python -m app.collectors.selby --source-id 8 --delay 1 --max-pages 5 --future-only
```

Use dry run for safe verification:

```bash
python -m app.collectors.vanwezel --source-id 1 --dry-run --max-pages 2
```
