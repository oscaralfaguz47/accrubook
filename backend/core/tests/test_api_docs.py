"""API docs (schema and Swagger UI) are served only where explicitly enabled."""

import os
import subprocess
import sys

import pytest
from django.conf import settings as project_settings
from django.urls import reverse

DOCS_URLS = [reverse("schema"), reverse("docs")]


def test_docs_are_disabled_when_the_variable_is_unset():
    env = {name: value for name, value in os.environ.items() if name != "DJANGO_API_DOCS_ENABLED"}
    result = subprocess.run(
        # A fresh process reads the settings from the environment from scratch.
        [
            sys.executable,
            "-c",
            "from django.conf import settings; print(settings.API_DOCS_ENABLED)",
        ],
        cwd=project_settings.BASE_DIR,
        env={**env, "DJANGO_SETTINGS_MODULE": "config.settings"},
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )

    assert result.stdout.strip() == "False"


@pytest.mark.parametrize("url", DOCS_URLS)
def test_docs_return_problem_404_when_disabled(client, settings, url):
    settings.API_DOCS_ENABLED = False

    response = client.get(url)

    assert response.status_code == 404
    assert response["Content-Type"] == "application/problem+json"


@pytest.mark.parametrize("url", DOCS_URLS)
def test_docs_are_served_when_enabled(client, settings, url):
    settings.API_DOCS_ENABLED = True

    response = client.get(url)

    assert response.status_code == 200


def test_swagger_ui_assets_are_pinned(client, settings):
    settings.API_DOCS_ENABLED = True

    html = client.get(reverse("docs")).content.decode()

    assert "swagger-ui-dist@5.35.1" in html
    assert "@latest" not in html
