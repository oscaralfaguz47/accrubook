"""gunicorn reads its settings from the environment and fails fast (ADR 0007)."""

import runpy

import pytest
from django.conf import settings

CONFIG_FILE = settings.BASE_DIR / "gunicorn.conf.py"


def load_config(monkeypatch, **env: str) -> dict:
    """Run gunicorn.conf.py the way gunicorn does and return the settings it defines."""
    monkeypatch.delenv("GUNICORN_WORKERS", raising=False)
    monkeypatch.delenv("DJANGO_LOG_JSON", raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    return runpy.run_path(str(CONFIG_FILE))


def test_workers_come_from_the_environment(monkeypatch):
    config = load_config(monkeypatch, GUNICORN_WORKERS="3")

    assert config["workers"] == 3


def test_workers_are_required(monkeypatch):
    with pytest.raises(RuntimeError, match="GUNICORN_WORKERS"):
        load_config(monkeypatch)


def test_both_logs_go_to_stdout_as_json_by_default(monkeypatch):
    logging_config = load_config(monkeypatch, GUNICORN_WORKERS="2")["logconfig_dict"]

    handler = logging_config["handlers"]["stdout"]
    assert handler["stream"] == "ext://sys.stdout"
    assert handler["formatter"] == "json"
    for logger in ("gunicorn.error", "gunicorn.access"):
        assert logging_config["loggers"][logger]["handlers"] == ["stdout"]


def test_logs_are_text_when_json_is_off(monkeypatch):
    config = load_config(monkeypatch, GUNICORN_WORKERS="2", DJANGO_LOG_JSON="false")

    assert config["logconfig_dict"]["handlers"]["stdout"]["formatter"] == "text"


def test_access_log_takes_bytes_from_content_length(monkeypatch):
    access_format = load_config(monkeypatch, GUNICORN_WORKERS="2")["access_log_format"]

    assert "%({content-length}o)s" in access_format
    assert "%(b)s" not in access_format
