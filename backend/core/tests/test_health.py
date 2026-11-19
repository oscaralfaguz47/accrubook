import logging
from unittest.mock import patch

import pytest
from django.db import DatabaseError
from django.urls import reverse

HEALTH_URL = reverse("core:health")


@pytest.mark.django_db
def test_health_returns_ok_when_database_is_reachable(client):
    response = client.get(HEALTH_URL)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_returns_503_and_logs_when_database_is_unavailable(client, caplog):
    with (
        patch("core.views.connection.cursor", side_effect=DatabaseError("connection refused")),
        caplog.at_level(logging.ERROR, logger="core.views"),
    ):
        response = client.get(HEALTH_URL)

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable"}
    assert "database is unavailable" in caplog.text


def test_health_rejects_non_get_methods(client):
    response = client.post(HEALTH_URL)

    assert response.status_code == 405
