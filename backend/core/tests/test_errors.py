import logging

import pytest
from django.test import RequestFactory
from rest_framework import exceptions, serializers
from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from core.errors import server_error_view

PROBLEM_CONTENT_TYPE = "application/problem+json"


class _AmountSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class _FailingView(APIView):
    """Test-only view: raises the exception named in the query string."""

    permission_classes = [AllowAny]

    def get(self, request):
        failure = request.query_params["fail"]
        if failure == "validation":
            _AmountSerializer(data={"amount": "abc"}).is_valid(raise_exception=True)
        if failure == "throttled":
            raise exceptions.Throttled(wait=30)
        raise RuntimeError("database password is hunter2")  # A bug with a secret in it.


def _call_failing_view(failure: str):
    request = APIRequestFactory().get("/api/test/", {"fail": failure})
    response = _FailingView.as_view()(request)
    response.render()
    return response


def test_validation_error_lists_the_errors_per_field():
    response = _call_failing_view("validation")

    assert response.status_code == 400
    assert response["Content-Type"] == PROBLEM_CONTENT_TYPE
    body = response.data
    assert body["code"] == "invalid"
    assert body["errors"] == {"amount": ["A valid number is required."]}


def test_drf_headers_are_kept():
    response = _call_failing_view("throttled")

    assert response.status_code == 429
    assert response["Retry-After"] == "30"
    assert response.data["code"] == "throttled"


def test_unexpected_error_is_logged_but_not_leaked(caplog):
    with caplog.at_level(logging.ERROR, logger="core.errors"):
        response = _call_failing_view("bug")

    assert response.status_code == 500
    assert response.data["detail"] == "An unexpected error occurred."
    assert "hunter2" not in response.content.decode()
    assert "Unhandled API error on GET /api/test/" in caplog.text
    assert "hunter2" in caplog.text  # The full error goes to the logs, for us.


@pytest.mark.django_db
def test_unknown_api_url_returns_problem_details(client):
    response = client.get("/api/does-not-exist/")

    assert response.status_code == 404
    assert response["Content-Type"] == PROBLEM_CONTENT_TYPE
    assert response.json()["code"] == "not_found"


@pytest.mark.django_db
def test_unknown_non_api_url_keeps_django_html_page(client):
    response = client.get("/does-not-exist/")

    assert response.status_code == 404
    assert response["Content-Type"].startswith("text/html")


@pytest.mark.parametrize(
    ("path", "expected_content_type"),
    [("/api/health/", PROBLEM_CONTENT_TYPE), ("/admin/", "text/html")],
)
def test_server_error_view_is_json_only_for_the_api(path, expected_content_type):
    response = server_error_view(RequestFactory().get(path))

    assert response.status_code == 500
    assert response["Content-Type"].startswith(expected_content_type)
