"""Serializers for the dining room and its reservations.

Read serializers shape the output; write serializers only validate the input
shape. The booking rules (is the table free?) live in
``reservations.services``.
"""

from rest_framework import serializers

from . import selectors
from .models import Reservation, Table


class TableSerializer(serializers.ModelSerializer):
    """Admin-facing representation of a table."""

    class Meta:
        model = Table
        fields = ("id", "number", "label", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class TableAvailabilitySerializer(serializers.ModelSerializer):
    """A table on the booking screen, with whether it can be selected.

    ``is_available`` comes from the annotation in
    ``selectors.table_availability``.
    """

    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Table
        fields = ("id", "number", "label", "is_available")


class ReservationSerializer(serializers.ModelSerializer):
    """Read representation of a reservation."""

    customer_username = serializers.CharField(
        source="customer.username", read_only=True
    )
    table_number = serializers.IntegerField(source="table.number", read_only=True)
    table_label = serializers.CharField(source="table.label", read_only=True)

    class Meta:
        model = Reservation
        fields = (
            "id",
            "customer",
            "customer_username",
            "table",
            "table_number",
            "table_label",
            "party_size",
            "status",
            "note",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "customer", "status", "created_at", "updated_at")


class ReservationCreateSerializer(serializers.Serializer):
    """Input shape for booking a table. The customer comes from the request.

    Limiting the queryset to bookable tables means a retired or non-existent
    table is rejected here, before any business logic runs.
    """

    table = serializers.PrimaryKeyRelatedField(queryset=selectors.bookable_tables())
    party_size = serializers.IntegerField(min_value=1)
    note = serializers.CharField(required=False, allow_blank=True, default="")


class ReservationStatusUpdateSerializer(serializers.Serializer):
    """Input shape for the admin-only status action."""

    status = serializers.ChoiceField(choices=Reservation.Status.choices)
