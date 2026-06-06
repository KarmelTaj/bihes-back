"""
Swagger / OpenAPI documentation URLs (drf-spectacular).

Included from core/urls.py.
"""
from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema', template_name='swagger_ui_dark.html'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema', template_name='redoc_dark.html'), name='redoc'),
]
