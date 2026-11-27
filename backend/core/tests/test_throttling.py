"""Anonymous throttling: keyed on the real client IP, never on a forgeable header."""

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from core.throttling import ClientIPAnonRateThrottle
from currencies.views import CurrencyViewSet

PROBLEM_CONTENT_TYPE = "application/problem+json"


class _OnePerMinute(ClientIPAnonRateThrottle):
    rate = "1/minute"


class _ThrottledView(APIView):
    """Test-only view: one anonymous request per minute per client."""

    permission_classes = [AllowAny]
    throttle_classes = [_OnePerMinute]

    def get(self, request):
        return Response({"ok": True})


def _get(**meta: str):
    request = APIRequestFactory().get("/api/test/", **meta)
    response = _ThrottledView.as_view()(request)
    response.render()
    return response


def test_request_over_the_limit_gets_problem_429():
    assert _get().status_code == 200

    response = _get()

    assert response.status_code == 429
    assert response["Content-Type"] == PROBLEM_CONTENT_TYPE
    assert "Retry-After" in response


def test_forged_x_forwarded_for_does_not_reset_the_limit(settings):
    settings.CLIENT_IP_HEADER = None  # No proxy, as in local development.

    assert _get(HTTP_X_FORWARDED_FOR="203.0.113.1").status_code == 200
    assert _get(HTTP_X_FORWARDED_FOR="203.0.113.2").status_code == 429


def test_behind_the_proxy_each_client_ip_has_its_own_limit(settings):
    settings.CLIENT_IP_HEADER = "HTTP_X_REAL_IP"

    assert _get(HTTP_X_REAL_IP="203.0.113.1").status_code == 200
    assert _get(HTTP_X_REAL_IP="203.0.113.2").status_code == 200
    assert _get(HTTP_X_REAL_IP="203.0.113.1").status_code == 429


def test_api_views_are_throttled_by_default():
    throttles = CurrencyViewSet().get_throttles()

    assert [type(throttle) for throttle in throttles] == [ClientIPAnonRateThrottle]
    assert throttles[0].rate == "60/minute"
