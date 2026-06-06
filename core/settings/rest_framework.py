"""
Django REST Framework and drf-spectacular (OpenAPI) settings.

Kept separate from ``base.py`` so API-layer configuration has a single, growing
home (authentication, permissions, pagination, throttling, …).
"""

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Logs every error and returns a consistent envelope splitting
    # field errors from general errors.
    "EXCEPTION_HANDLER": "core.api.exceptions.custom_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Bihes's API",
    "DESCRIPTION": "API documentation",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Serve Swagger UI / ReDoc assets locally (drf-spectacular-sidecar)
    # instead of from a CDN, so the docs work fully offline.
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
}
