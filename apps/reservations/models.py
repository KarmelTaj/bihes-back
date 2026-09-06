"""Reservation domain: the dining room's tables and the bookings that hold them.

A ``Table`` is a real row, so admins can reshape the floor plan through the API
instead of a deploy, and each table can carry its own identity (a label, and
later a zone or a photo). A table is "occupied" for exactly as long as it has
an ``ACTIVE`` reservation; cancelling or completing one frees it for the next
customer.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Table(models.Model):
    """One physical table in the dining room."""

    number = models.PositiveIntegerField(
        unique=True,
        validators=[MinValueValidator(1)],
        help_text="The number printed on the table. Unique across the room.",
    )
    label = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional human name, e.g. 'Booth by the window'.",
    )
    is_active = models.BooleanField(
        default=True, help_text="Inactive tables can't be booked and are hidden."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("number",)

    def __str__(self) -> str:
        return self.label or f"Table {self.number}"


class Reservation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    OCCUPYING_STATUSES = (Status.ACTIVE,)

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations"
    )
    table = models.ForeignKey(
        Table, on_delete=models.PROTECT, related_name="reservations"
    )
    party_size = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="How many people the booking is for. Not capped by table size.",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    note = models.TextField(blank=True, help_text="Optional note from the customer.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            # two concurrent requests for the same free table can both pass 
            # the service's occupancy check, and only one of them may win.
            models.UniqueConstraint(
                fields=["table"],
                condition=models.Q(status="active"),
                name="unique_active_reservation_per_table",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.table} for {self.party_size} "
            f"by {self.customer} ({self.status})"
        )

    @property
    def is_occupying(self) -> bool:
        """True while this reservation still holds its table."""
        return self.status in self.OCCUPYING_STATUSES
