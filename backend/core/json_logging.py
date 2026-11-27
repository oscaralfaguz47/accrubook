"""One JSON object per log line, in the shape Railway parses (ADR 0007).

Railway reads `message` and `level` (debug, info, warn, error) from single-line JSON on
stdout; every other key becomes an attribute to filter on, such as `@logger:core.views`.
"""

import json
import logging
from datetime import UTC, datetime


def railway_level(levelno: int) -> str:
    """Map a Python level to the closest of Railway's four levels."""
    if levelno >= logging.ERROR:
        return "error"
    if levelno >= logging.WARNING:
        return "warn"
    if levelno >= logging.INFO:
        return "info"
    return "debug"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": railway_level(record.levelno),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)
