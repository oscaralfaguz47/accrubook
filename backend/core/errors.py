"""Consistent API errors in the RFC 9457 "Problem Details" format.

Every error the API returns has the same shape, whatever caused it:

    {
        "type": "about:blank",
        "title": "Not Found",
        "status": 404,
        "detail": "Not found.",
        "code": "not_found",
        "instance": "/api/v1/currencies/XXX/"
    }

Validation errors add an "errors" object with the messages for each field.
"""

import logging
from http import HTTPStatus
from typing import Any

from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.views import defaults
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

PROBLEM_CONTENT_TYPE = "application/problem+json"
API_PATH_PREFIX = "/api/"
SERVER_ERROR_DETAIL = "An unexpected error occurred."


def build_problem(*, status: int, detail: str, code: str, instance: str) -> dict[str, Any]:
    """Build a Problem Details body. The title is the standard HTTP reason phrase."""
    return {
        "type": "about:blank",
        "title": HTTPStatus(status).phrase,
        "status": status,
        "detail": detail,
        "code": code,
        "instance": instance,
    }


def problem_details_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    """DRF EXCEPTION_HANDLER: turn every exception raised in an API view into Problem Details."""
    request = context["request"]

    # Translate Django's exceptions to DRF's, so they get a status code and an error code.
    # The generic message also avoids leaking model names ("No Currency matches...").
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    # DRF builds the response and its headers (WWW-Authenticate, Retry-After...).
    response = exception_handler(exc, context)

    if response is None:
        # Not an API exception: it's a bug. Log the full traceback, never send it to the client.
        logger.error("Unhandled API error on %s %s", request.method, request.path, exc_info=exc)
        response = Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)
        problem = build_problem(
            status=response.status_code,
            detail=SERVER_ERROR_DETAIL,
            code="server_error",
            instance=request.path,
        )
    elif isinstance(exc, exceptions.ValidationError):
        problem = build_problem(
            status=response.status_code,
            detail="The request contains invalid data.",
            code="invalid",
            instance=request.path,
        )
        problem["errors"] = response.data
    else:
        problem = build_problem(
            status=response.status_code,
            detail=str(exc.detail),
            code=exc.get_codes(),
            instance=request.path,
        )

    response.data = problem
    response.content_type = PROBLEM_CONTENT_TYPE
    return response


def not_found_view(request: HttpRequest, exception: Exception) -> HttpResponse:
    """handler404: URLs that match no route. JSON for the API, Django's HTML page elsewhere."""
    if not request.path.startswith(API_PATH_PREFIX):
        return defaults.page_not_found(request, exception)
    problem = build_problem(
        status=HTTPStatus.NOT_FOUND,
        detail="The requested resource was not found.",
        code="not_found",
        instance=request.path,
    )
    return JsonResponse(problem, status=HTTPStatus.NOT_FOUND, content_type=PROBLEM_CONTENT_TYPE)


def server_error_view(request: HttpRequest) -> HttpResponse:
    """handler500: crashes outside DRF views. Django already logged the traceback."""
    if not request.path.startswith(API_PATH_PREFIX):
        return defaults.server_error(request)
    problem = build_problem(
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
        detail=SERVER_ERROR_DETAIL,
        code="server_error",
        instance=request.path,
    )
    return JsonResponse(
        problem, status=HTTPStatus.INTERNAL_SERVER_ERROR, content_type=PROBLEM_CONTENT_TYPE
    )
