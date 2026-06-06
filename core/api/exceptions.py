"""
Custom DRF exception handler.

Wraps DRF's default handler to:

* log every error (with the request's ``request_id`` already in context via the
  middleware), and
* return a consistent error envelope that separates **field errors** (tied to a
  specific serializer field) from **general errors** (everything not bound to a
  field — ``non_field_errors``, ``detail``, plain-string messages, and
  unexpected server errors).

Response shape::

    {
        "request_id": "…",
        "status_code": 400,
        "field_errors": {"email": ["This field is required."]},
        "general_errors": ["Unable to log in with provided credentials."]
    }
"""

from __future__ import annotations

import structlog
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = structlog.get_logger("api.error")

# Keys DRF uses for errors that are not attached to a particular field.
_GENERAL_ERROR_KEYS = {"non_field_errors", "detail"}


def _as_list(value):
    """Normalise a DRF error value into a flat list of strings."""
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _split_errors(data):
    """Split DRF error ``data`` into (field_errors, general_errors)."""
    field_errors: dict[str, list[str]] = {}
    general_errors: list[str] = []

    if isinstance(data, dict):
        for key, value in data.items():
            if key in _GENERAL_ERROR_KEYS:
                general_errors.extend(_as_list(value))
            else:
                field_errors[key] = _as_list(value)
    elif isinstance(data, list):
        general_errors.extend(_as_list(data))
    else:
        general_errors.append(str(data))

    return field_errors, general_errors


def custom_exception_handler(exc, context):
    request = context.get("request")
    view = context.get("view")
    request_id = getattr(request, "request_id", None)

    log = logger.bind(
        exc_type=exc.__class__.__name__,
        view=view.__class__.__name__ if view is not None else None,
    )

    # Let DRF map known exceptions (ValidationError, NotAuthenticated, …) to a
    # response. Returns None for exceptions DRF doesn't recognise.
    response = drf_exception_handler(exc, context)

    if response is not None:
        field_errors, general_errors = _split_errors(response.data)

        log.warning(
            "api_error",
            status_code=response.status_code,
            field_errors=field_errors,
            general_errors=general_errors,
        )

        response.data = {
            "request_id": request_id,
            "status_code": response.status_code,
            "field_errors": field_errors,
            "general_errors": general_errors,
        }
        return response

    # Unhandled exception -> 500. We're inside DRF's `except` block, so
    # `.exception()` captures the active traceback.
    log.exception("unhandled_exception")

    return Response(
        {
            "request_id": request_id,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "field_errors": {},
            "general_errors": ["A server error occurred. Please try again later."],
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
