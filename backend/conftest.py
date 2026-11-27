import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APIClient


@pytest.fixture(scope="session", autouse=True)
def _collected_static(tmp_path_factory):
    """Collect static files once, as the image build does.

    Production storage needs the manifest: without it, any page with {% static %}
    (the admin) fails with "Missing staticfiles manifest entry".
    """
    static_root = tmp_path_factory.mktemp("staticfiles")
    with override_settings(STATIC_ROOT=static_root):
        call_command("collectstatic", "--noinput", verbosity=0)
        yield static_root


@pytest.fixture(autouse=True)
def _clear_cache():
    """Every test starts with empty throttle counters, whatever ran before it."""
    cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    """An unauthenticated DRF test client."""
    return APIClient()
