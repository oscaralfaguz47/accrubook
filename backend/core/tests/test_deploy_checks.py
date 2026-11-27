"""Production settings pass Django's deployment checklist (`check --deploy`)."""

import os
import secrets
import subprocess
import sys

from django.conf import settings


def run_deploy_check(**overrides: str) -> subprocess.CompletedProcess[str]:
    """Run `check --deploy` in a fresh process with production-like variables."""
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings",
        "DJANGO_DEBUG": "false",
        "DJANGO_SECRET_KEY": secrets.token_urlsafe(50),
        "DJANGO_ALLOWED_HOSTS": "api.example.com",
    }
    env.pop("DJANGO_HTTPS_ONLY", None)  # production relies on the secure default
    env.update(overrides)
    return subprocess.run(
        [sys.executable, "-m", "django", "check", "--deploy", "--fail-level", "WARNING"],
        cwd=settings.BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def test_production_settings_pass_the_deploy_checklist():
    result = run_deploy_check()

    assert result.returncode == 0, result.stdout + result.stderr


def test_https_only_off_fails_the_deploy_checklist():
    result = run_deploy_check(DJANGO_HTTPS_ONLY="false")

    assert result.returncode != 0
    assert "security.W008" in result.stdout + result.stderr
