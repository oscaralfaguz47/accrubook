import logging

from django.db import DatabaseError, connection
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    """Readiness probe used by the hosting platform to decide if the API can take traffic."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        logger.exception("Health check failed: database is unavailable")
        return JsonResponse({"status": "degraded", "database": "unavailable"}, status=503)

    return JsonResponse({"status": "ok", "database": "ok"})
