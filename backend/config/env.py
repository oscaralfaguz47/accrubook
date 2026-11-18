"""Typed helpers for reading configuration from environment variables."""

import os


def env_str(name: str, default: str | None = None) -> str:
    """Return a required string variable, or ``default`` when one is given."""
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    """Parse a comma-separated variable into a list, ignoring empty items."""
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]