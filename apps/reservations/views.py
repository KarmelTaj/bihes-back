"""Reservation endpoints.

Customers see the dining room, book a free table, and cancel their own
booking; admins shape the floor plan and drive reservation status. The
viewsets stay thin: querysets come from ``reservations.selectors``, mutations
go through ``reservations.services``.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrReadOnly, IsAdminRole, IsOwnerOrAdmin

from . import selectors, services
from .models import Reservation
from .serializers import (
    ReservationCreateSerializer,
    ReservationSerializer,
    ReservationStatusUpdateSerializer,
    TableAvailabilitySerializer,
    TableSerializer,
)


class TableViewSet(viewsets.ModelViewSet):
    """Admin-managed floor plan. Anyone may read it; only admins reshape it."""

    serializer_class = TableSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ("is_active",)

    def get_queryset(self):
        return selectors.table_list()

    def perform_create(self, serializer):
        serializer.instance = services.table_create(**serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = services.table_update(
            table=serializer.instance, data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        services.table_delete(table=instance)


class TableAvailabilityView(generics.ListAPIView):
    """Every bookable table and whether it is free right now.

    The booking screen calls this first: tables that come back with
    ``is_available: false`` are held by someone else and can't be selected.
    """

    serializer_class = TableAvailabilitySerializer

    def get_queryset(self):
        return selectors.table_availability()


class ReservationViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """List/retrieve/create reservations, plus cancel and admin status actions."""

    filterset_fields = ("status", "table")

    def get_queryset(self):
        # drf-spectacular introspects this with an AnonymousUser; bail early.
        if getattr(self, "swagger_fake_view", False):
            return Reservation.objects.none()
        return selectors.reservation_list(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return ReservationCreateSerializer
        if self.action == "set_status":
            return ReservationStatusUpdateSerializer
        return ReservationSerializer

    def get_permissions(self):
        if self.action in ("retrieve", "cancel"):
            return [IsOwnerOrAdmin()]
        if self.action == "set_status":
            return [IsAdminRole()]
        return super().get_permissions()

    @extend_schema(responses=ReservationSerializer)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = services.reservation_create(
            customer=request.user, **serializer.validated_data
        )
        output = ReservationSerializer(
            reservation, context=self.get_serializer_context()
        )
        return Response(output.data, status=status.HTTP_201_CREATED)

    @extend_schema(request=None, responses=ReservationSerializer)
    @action(detail=True, methods=["patch"])
    def cancel(self, request, pk=None):
        """Give the table back. Available to the booking's owner or an admin."""
        reservation = services.reservation_cancel(reservation=self.get_object())
        output = ReservationSerializer(
            reservation, context=self.get_serializer_context()
        )
        return Response(output.data)

    @extend_schema(responses=ReservationSerializer)
    @action(detail=True, methods=["patch"], url_path="status")
    def set_status(self, request, pk=None):
        reservation = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = services.reservation_set_status(
            reservation=reservation, status=serializer.validated_data["status"]
        )
        output = ReservationSerializer(
            reservation, context=self.get_serializer_context()
        )
        return Response(output.data)
