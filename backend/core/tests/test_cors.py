"""CORS: only the configured frontend origins may call the API from a browser."""

import pytest
from django.urls import reverse

ALLOWED_ORIGIN = "http://localhost:5173"
OTHER_ORIGIN = "https://evil.example"

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def cors_origins(settings):
    """Pin the allowed origins so the tests don't depend on the local .env."""
    settings.CORS_ALLOWED_ORIGINS = [ALLOWED_ORIGIN]


def test_allowed_origin_gets_cors_headers(api_client):
    response = api_client.get(reverse("currencies:currency-list"), HTTP_ORIGIN=ALLOWED_ORIGIN)

    assert response.status_code == 200
    assert response["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN
    assert "origin" in response["Vary"].lower()


def test_unknown_origin_gets_no_cors_headers(api_client):
    response = api_client.get(reverse("currencies:currency-list"), HTTP_ORIGIN=OTHER_ORIGIN)

    # CORS is enforced by the browser, not by the server: the response is still sent,
    # but without the header the browser refuses to hand it to the calling page.
    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response


def test_preflight_from_allowed_origin_is_accepted(api_client):
    response = api_client.options(
        reverse("currencies:currency-list"),
        HTTP_ORIGIN=ALLOWED_ORIGIN,
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization",
    )

    assert response.status_code == 200
    assert response["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN
    assert "GET" in response["Access-Control-Allow-Methods"]
    assert "authorization" in response["Access-Control-Allow-Headers"]


def test_credentials_are_not_allowed(api_client):
    response = api_client.get(reverse("currencies:currency-list"), HTTP_ORIGIN=ALLOWED_ORIGIN)

    assert "Access-Control-Allow-Credentials" not in response


def test_non_api_paths_get_no_cors_headers(client):
    response = client.get(reverse("admin:login"), HTTP_ORIGIN=ALLOWED_ORIGIN)

    assert "Access-Control-Allow-Origin" not in response
