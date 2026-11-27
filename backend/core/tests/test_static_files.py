"""Production serves static files from the app (WhiteNoise): hashed, compressed, cached.

The manifest comes from the session-wide collectstatic in the root conftest.py.
"""

from django.templatetags.static import static

ADMIN_CSS = "admin/css/base.css"


def test_static_urls_carry_a_content_hash():
    url = static(ADMIN_CSS)

    assert url != f"/static/{ADMIN_CSS}"
    assert url.startswith("/static/admin/css/base.")
    assert url.endswith(".css")


def test_hashed_files_are_served_compressed_and_cached_forever(client):
    response = client.get(static(ADMIN_CSS), HTTP_ACCEPT_ENCODING="gzip", secure=True)

    assert response.status_code == 200
    assert response["Cache-Control"] == "max-age=315360000, public, immutable"
    assert response["Content-Encoding"] == "gzip"
    assert response["Vary"] == "Accept-Encoding"
