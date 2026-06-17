"""Serializers for reading, placing, and updating orders.

Read serializers shape the output; write serializers only validate the input
shape. Business rules (availability, price snapshot, atomicity) live in
``orders.services``.
"""

from rest_framework import serializers

from apps.menu.models import MenuItem

from .models import Order, OrderItem


class OrderItemReadSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = ("id", "menu_item", "menu_item_name", "quantity", "unit_price", "subtotal")


class OrderItemWriteSerializer(serializers.Serializer):
    """Input for a single line of a new order."""

    menu_item = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())
    quantity = serializers.IntegerField(min_value=1)


class OrderSerializer(serializers.ModelSerializer):
    """Read representation of an order with its items and computed total."""

    items = OrderItemReadSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    customer_username = serializers.CharField(
        source="customer.username", read_only=True
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "customer",
            "customer_username",
            "status",
            "note",
            "items",
            "total_price",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "customer", "status", "created_at", "updated_at")


class OrderCreateSerializer(serializers.Serializer):
    """Input shape for placing a new order. The customer comes from the request."""

    note = serializers.CharField(required=False, allow_blank=True, default="")
    items = OrderItemWriteSerializer(many=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("An order must contain at least one item.")
        return items


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Input shape for the admin-only status action."""

    status = serializers.ChoiceField(choices=Order.Status.choices)
