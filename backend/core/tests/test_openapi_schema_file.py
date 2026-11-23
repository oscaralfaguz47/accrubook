"""The committed OpenAPI schema must always match the code.

The frontend generates its TypeScript types from ``backend/openapi.yaml``.
If that file is stale, the frontend compiles against an API that no longer
exists, so this test fails the build until someone runs ``make schema``.
"""

from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command

SCHEMA_FILE_NAME = "openapi.yaml"
FIX_HINT = "Run `make schema` and commit the result."


def test_committed_openapi_schema_is_up_to_date():
    schema_file = Path(settings.BASE_DIR) / SCHEMA_FILE_NAME
    generated = StringIO()

    call_command("spectacular", "--validate", "--fail-on-warn", stdout=generated)

    assert schema_file.exists(), f"{SCHEMA_FILE_NAME} is missing. {FIX_HINT}"
    assert schema_file.read_text(encoding="utf-8") == generated.getvalue(), (
        f"{SCHEMA_FILE_NAME} is out of date. {FIX_HINT}"
    )
