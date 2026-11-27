"""Environment helpers: a valid value, or a startup error."""

import pytest

from config.env import env_bool, env_positive_int

NAME = "ACCRUBOOK_TEST_FLAG"


@pytest.mark.parametrize("value", ["1", "true", "TRUE", " yes ", "on"])
def test_true_values(monkeypatch, value):
    monkeypatch.setenv(NAME, value)

    assert env_bool(NAME) is True


@pytest.mark.parametrize("value", ["0", "false", "False", " no ", "off"])
def test_false_values_override_a_true_default(monkeypatch, value):
    monkeypatch.setenv(NAME, value)

    assert env_bool(NAME, default=True) is False


@pytest.mark.parametrize("default", [True, False])
def test_unset_variable_returns_the_default(monkeypatch, default):
    monkeypatch.delenv(NAME, raising=False)

    assert env_bool(NAME, default=default) is default


@pytest.mark.parametrize("value", ["flase", "", "2", "enabled"])
def test_invalid_value_fails_fast(monkeypatch, value):
    monkeypatch.setenv(NAME, value)

    with pytest.raises(RuntimeError, match=NAME):
        env_bool(NAME)


@pytest.mark.parametrize(("value", "expected"), [("1", 1), ("4", 4), (" 2 ", 2)])
def test_positive_int_values(monkeypatch, value, expected):
    monkeypatch.setenv(NAME, value)

    assert env_positive_int(NAME) == expected


def test_positive_int_is_required(monkeypatch):
    monkeypatch.delenv(NAME, raising=False)

    with pytest.raises(RuntimeError, match=NAME):
        env_positive_int(NAME)


@pytest.mark.parametrize("value", ["0", "-1", "+2", "two", "", "2.5", "1_000"])
def test_invalid_positive_int_fails_fast(monkeypatch, value):
    monkeypatch.setenv(NAME, value)

    with pytest.raises(RuntimeError, match=NAME):
        env_positive_int(NAME)
