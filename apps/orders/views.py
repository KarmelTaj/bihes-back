"""Order endpoints.

Customers place and view their own orders; admins see every order and are the
only ones who can change an order's status. The viewset stays thin: querysets
come from ``orders.selectors``, mutations go through ``orders.services``.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminRole, IsOwnerOrAdmin

from . import selectors, services
from .models import Order
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusUpdateSerializer,
)


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """List/retrieve/create orders, plus an admin-only status action."""

    def get_queryset(self):
        # drf-spectacular introspects this with an AnonymousUser; bail early.
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        return selectors.order_list(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action == "set_status":
            return OrderStatusUpdateSerializer
        return OrderSerializer

    def get_permissions(self):
        if self.action == "retrieve":
            return [IsOwnerOrAdmin()]
        if self.action == "set_status":
            return [IsAdminRole()]
        return super().get_permissions()

    @extend_schema(responses=OrderSerializer)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = services.order_create(
            customer=request.user, **serializer.validated_data
        )
        output = OrderSerializer(order, context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_201_CREATED)

    @extend_schema(responses=OrderSerializer)
    @action(detail=True, methods=["patch"], url_path="status")
    def set_status(self, request, pk=None):
        order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = services.order_set_status(
            order=order, status=serializer.validated_data["status"]
        )
        output = OrderSerializer(order, context=self.get_serializer_context())
        return Response(output.data)
