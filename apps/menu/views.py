"""Menu endpoints. Customers browse; admins manage.

ViewSets stay thin: querysets come from ``menu.selectors``, mutations go
through ``menu.services``.
"""

from rest_framework import viewsets

from apps.accounts.permissions import IsAdminOrReadOnly

from . import selectors, services
from .serializers import CategorySerializer, MenuItemSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ("is_active",)

    def get_queryset(self):
        return selectors.category_list()

    def perform_create(self, serializer):
        serializer.instance = services.category_create(**serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = services.category_update(
            category=serializer.instance, data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        services.category_delete(category=instance)


class MenuItemViewSet(viewsets.ModelViewSet):
    serializer_class = MenuItemSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ("category", "is_available")

    def get_queryset(self):
        return selectors.menu_item_list()

    def perform_create(self, serializer):
        serializer.instance = services.menu_item_create(**serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = services.menu_item_update(
            menu_item=serializer.instance, data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        services.menu_item_delete(menu_item=instance)
