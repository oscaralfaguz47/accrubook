"""Production logs: one JSON object per line on stdout, in the shape Railway parses."""

import json
import logging
import os
import subprocess
import sys

import pytest
from django.conf import settings

from core.json_logging import JsonFormatter


def _record(level: int, msg: str, *args: object, exc_info=None) -> logging.LogRecord:
    return logging.LogRecord("accrubook.test", level, __file__, 1, msg, args, exc_info)


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        (logging.DEBUG, "debug"),
        (logging.INFO, "info"),
        (logging.WARNING, "warn"),
        (logging.ERROR, "error"),
        (logging.CRITICAL, "error"),
    ],
)
def test_levels_use_railway_names(level, expected):
    entry = json.loads(JsonFormatter().format(_record(level, "hello")))

    assert entry["level"] == expected


def test_message_is_formatted_with_its_arguments():
    entry = json.loads(JsonFormatter().format(_record(logging.INFO, "disk at %d%%", 91)))

    assert entry["message"] == "disk at 91%"
    assert entry["logger"] == "accrubook.test"


def test_traceback_stays_on_one_line():
    try:
        raise ValueError("boom")
    except ValueError:
        line = JsonFormatter().format(_record(logging.ERROR, "failed", exc_info=sys.exc_info()))

    assert "\n" not in line
    assert "ValueError: boom" in json.loads(line)["exception"]


def test_production_logs_are_json_on_stdout():
    env = {name: value for name, value in os.environ.items() if name != "DJANGO_LOG_JSON"}
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import django, logging; django.setup(); "
            "logging.getLogger('accrubook.test').warning('hello')",
        ],
        cwd=settings.BASE_DIR,
        env={**env, "DJANGO_SETTINGS_MODULE": "config.settings"},
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )

    entry = json.loads(result.stdout.strip().splitlines()[-1])
    assert entry["level"] == "warn"
    assert entry["message"] == "hello"
    assert result.stderr == ""
