"""Write-side business logic for the orders app.

The order lifecycle rules live here: availability checks, the unit-price
snapshot, atomicity of order creation, and status changes. Serializers only
validate the input shape.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import Order, OrderItem

User = get_user_model()


@transaction.atomic
def order_create(*, customer: User, items: list[dict], note: str = "") -> Order:
    """Place a new order for ``customer``.

    ``items`` is a list of ``{"menu_item": MenuItem, "quantity": int}`` dicts
    (as produced by ``OrderItemWriteSerializer``). Each line snapshots the menu
    item's current price so later menu price changes don't rewrite the history
    of past orders.
    """
    unavailable = [
        line["menu_item"].name for line in items if not line["menu_item"].is_available
    ]
    if unavailable:
        raise serializers.ValidationError(
            {"items": [f"These items are not available: {', '.join(unavailable)}."]}
        )

    order = Order.objects.create(customer=customer, note=note)
    OrderItem.objects.bulk_create(
        OrderItem(
            order=order,
            menu_item=line["menu_item"],
            quantity=line["quantity"],
            unit_price=line["menu_item"].price,
        )
        for line in items
    )
    return order


def order_set_status(*, order: Order, status: str) -> Order:
    """Admin action: move an order to a new status."""
    order.status = status
    order.save(update_fields=["status", "updated_at"])
    return order
