"""
Swagger / OpenAPI documentation URLs (drf-spectacular).

Included from core/urls.py.
"""
from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
)

# The Swagger UI itself is served at the site root (see core/urls.py); this
# module exposes the schema it consumes and the alternative ReDoc renderer.
urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
