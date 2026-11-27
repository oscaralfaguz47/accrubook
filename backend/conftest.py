import pytest
from django.core.cache import cache
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def _clear_cache():
    """Every test starts with empty throttle counters, whatever ran before it."""
    cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    """An unauthenticated DRF test client."""
    return APIClient()
