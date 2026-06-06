"""
Request-scoped logging middleware.

Assigns a unique ID to every incoming request and binds it (along with a few
request details) into structlog's context vars, so *all* log lines emitted
while handling that request automatically carry the ``request_id``. The ID is
also echoed back in the ``X-Request-ID`` response header so clients/proxies can
correlate a response with its server-side logs.
"""

from __future__ import annotations

import time
import uuid

import structlog

logger = structlog.get_logger("request")

# Header clients/proxies can use to supply their own correlation id; if absent
# we generate one.
REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware:
    """Bind a unique ``request_id`` to the logging context for each request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start from a clean context so ids never leak between requests on a
        # reused worker thread.
        structlog.contextvars.clear_contextvars()

        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        # Expose on the request object too, so views / the exception handler
        # can read it without touching structlog internals.
        request.request_id = request_id

        # Bound into the context so every log line emitted while handling this
        # request (including the exception handler) carries these fields.
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.path,
        )

        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        response[REQUEST_ID_HEADER] = request_id

        # A single summary line per request (2xx included). request_id, method
        # and path come from the bound context above.
        logger.info(
            "request_finished",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        structlog.contextvars.clear_contextvars()
        return response
