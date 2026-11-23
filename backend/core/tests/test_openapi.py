from django.core.management import call_command


def test_openapi_schema_is_valid_and_complete(tmp_path):
    # --fail-on-warn: if drf-spectacular can't document an endpoint, the test fails.
    call_command(
        "spectacular",
        "--validate",
        "--fail-on-warn",
        "--file",
        str(tmp_path / "schema.yaml"),
    )
