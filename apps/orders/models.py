"""Order domain: a customer's order and its line items."""

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.menu.models import MenuItem


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    note = models.TextField(blank=True, help_text="Optional note from the customer.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Order #{self.pk} by {self.customer} ({self.status})"

    @property
    def total_price(self) -> Decimal:
        return sum((item.subtotal for item in self.items.all()), Decimal("0.00"))


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(
        MenuItem, on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    # Snapshot of the menu item's price at order time, so later menu price
    # changes don't rewrite the history of past orders.
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.quantity} x {self.menu_item.name}"

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity
