# Logging Setup

This document describes the logging configuration for the SRQ Happenings API.

## Overview

The application uses Python's standard `logging` module with structured logging support. In development, logs are formatted with colors for readability. In production, logs are output as JSON for easy parsing by log aggregation tools.

## Configuration

Logging is configured via environment variables:

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: `INFO`
- `LOG_FORMAT`: Log format (`json` or `text`). Default: `text` for development, `json` for production
- `LOG_ENV`: Environment name (used to determine default format). Default: `development`

### Example Environment Variables

```bash
# Development (readable format)
LOG_LEVEL=DEBUG
LOG_FORMAT=text
LOG_ENV=development

# Production (JSON format)
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_ENV=production
```

## Usage

### Getting a Logger

In any module, get a logger using:

```python
import logging

logger = logging.getLogger(__name__)
```

Or use the convenience function:

```python
from app.core.logging import get_logger

logger = get_logger(__name__)
```

### Logging Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially problematic situations
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors that may cause the application to stop

### Basic Logging

```python
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### Structured Logging with Extra Context

Use the `extra` parameter to add structured data to logs:

```python
logger.info(
    "Processing source item",
    extra={
        "source_id": source.id,
        "item_id": item.id,
        "status": "processing",
    },
)
```

In JSON format, this will output:
```json
{
  "timestamp": "2024-01-15 10:30:45",
  "level": "INFO",
  "logger": "app.services.ingest_source_items",
  "message": "Processing source item",
  "source_id": 1,
  "item_id": 42,
  "status": "processing"
}
```

### Logging Exceptions

Use `exc_info=True` to include exception tracebacks:

```python
try:
    # some operation
    pass
except Exception as e:
    logger.error(
        "Operation failed",
        extra={"operation": "fetch_ics", "url": url},
        exc_info=True,
    )
```

Or use `logger.exception()` which automatically includes exception info:

```python
try:
    # some operation
    pass
except Exception as e:
    logger.exception(
        "Operation failed",
        extra={"operation": "fetch_ics", "url": url},
    )
```

## Log Format Examples

### Text Format (Development)

```
2024-01-15 10:30:45 | INFO     | app.routers.admin | Starting source ingestion | source_id=1
2024-01-15 10:30:46 | WARNING  | app.services.ingest_source_items | Error processing source item | source_id=1, item_id=42, error_type=RequestException
```

### JSON Format (Production)

```json
{"timestamp": "2024-01-15 10:30:45", "level": "INFO", "logger": "app.routers.admin", "message": "Starting source ingestion", "source_id": 1}
{"timestamp": "2024-01-15 10:30:46", "level": "WARNING", "logger": "app.services.ingest_source_items", "message": "Error processing source item", "source_id": 1, "item_id": 42, "error_type": "RequestException"}
```

## Best Practices

1. **Use appropriate log levels**: Don't log everything as INFO. Use DEBUG for detailed information, INFO for important events, WARNING for potential issues, and ERROR/CRITICAL for failures.

2. **Add context with `extra`**: Include relevant context in logs using the `extra` parameter. This makes logs more useful for debugging and monitoring.

3. **Log at boundaries**: Log at the start and end of important operations (API requests, ingestion jobs, etc.).

4. **Don't log sensitive data**: Avoid logging passwords, API keys, or other sensitive information.

5. **Use structured logging**: Prefer structured logging with `extra` over string formatting for better log parsing.

6. **Include request IDs**: For distributed systems, include request IDs or correlation IDs in logs to trace requests across services.

## Third-Party Logger Configuration

The following third-party loggers are configured to reduce noise:

- `uvicorn`: Set to WARNING level
- `uvicorn.access`: Set to INFO level (access logs)
- `sqlalchemy.engine`: Set to WARNING level
- `sqlalchemy.pool`: Set to WARNING level

To see SQL queries in development, you can temporarily set `sqlalchemy.engine` to DEBUG:

```python
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
```

## Integration with Log Aggregation Tools

The JSON format is designed to work with log aggregation tools like:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Loki** (Grafana Loki)
- **CloudWatch** (AWS)
- **Datadog**
- **Splunk**

These tools can parse the JSON logs and extract fields for searching, filtering, and visualization.
