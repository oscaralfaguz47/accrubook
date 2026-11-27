from collections.abc import Callable
from functools import wraps

from django.conf import settings
from django.contrib import admin
from django.http import Http404, HttpRequest, HttpResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

handler404 = "core.errors.not_found_view"
handler500 = "core.errors.server_error_view"

View = Callable[..., HttpResponse]


def api_docs_only(view: View) -> View:
    """Serve ``view`` only where API docs are enabled; elsewhere the URL is a plain 404."""

    @wraps(view)
    def wrapper(request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        if not settings.API_DOCS_ENABLED:
            raise Http404
        return view(request, *args, **kwargs)

    return wrapper


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("api/v1/", include("currencies.urls")),
    path("api/schema/", api_docs_only(SpectacularAPIView.as_view()), name="schema"),
    path(
        "api/docs/",
        api_docs_only(SpectacularSwaggerView.as_view(url_name="schema")),
        name="docs",
    ),
]
