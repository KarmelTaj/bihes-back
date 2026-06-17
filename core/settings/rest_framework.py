"""
Django REST Framework and drf-spectacular (OpenAPI) settings.

Kept separate from ``base.py`` so API-layer configuration has a single, growing
home (authentication, permissions, pagination, throttling, …).
"""

from datetime import timedelta

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Logs every error and returns a consistent envelope splitting
    # field errors from general errors.
    "EXCEPTION_HANDLER": "core.api.exceptions.custom_exception_handler",
    # Stateless JWT auth for all endpoints. Individual views opt out
    # (e.g. registration uses AllowAny).
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
}

# djangorestframework-simplejwt — access/refresh token lifetimes.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
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
