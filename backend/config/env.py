"""Typed helpers for reading configuration from environment variables."""

import os
import re


def env_str(name: str, default: str | None = None) -> str:
    """Return a required string variable, or ``default`` when one is given."""
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


def env_bool(name: str, default: bool = False) -> bool:
    """Return a boolean variable, or ``default`` when it is unset.

    Any other value fails fast: a typo must not silently switch a setting off.
    """
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise RuntimeError(
        f"Invalid boolean in environment variable {name} (use true/false, yes/no, on/off or 1/0)"
    )


def env_positive_int(name: str) -> int:
    """Return a required whole number of 1 or more.

    Anything else fails fast, including values int() would accept ("+2", "1_000"):
    a typo must not silently change how the service runs.
    """
    value = env_str(name).strip()
    if not re.fullmatch(r"[0-9]+", value) or int(value) < 1:
        raise RuntimeError(
            f"Invalid value in environment variable {name} (use a whole number of 1 or more)"
        )
    return int(value)


def env_list(name: str, default: str = "") -> list[str]:
    """Parse a comma-separated variable into a list, ignoring empty items."""
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]
