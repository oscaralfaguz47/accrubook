import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from currencies.models import Currency

pytestmark = pytest.mark.django_db


def test_str_returns_the_code():
    assert str(Currency.objects.get(code="USD")) == "USD"


@pytest.mark.parametrize("code", ["usd", "US", "US1"])
def test_database_rejects_an_invalid_code(code):
    with pytest.raises(IntegrityError):
        Currency.objects.create(code=code, name="Invalid", decimal_places=2)


def test_database_rejects_more_than_four_decimal_places():
    with pytest.raises(IntegrityError):
        Currency.objects.create(code="ABC", name="Too precise", decimal_places=5)


def test_validators_report_every_invalid_field():
    currency = Currency(code="us", name="Invalid", decimal_places=9)

    with pytest.raises(ValidationError) as error:
        currency.full_clean()

    assert set(error.value.message_dict) == {"code", "decimal_places"}
