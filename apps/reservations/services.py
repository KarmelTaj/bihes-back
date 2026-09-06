"""Write-side business logic for the reservations app.

The booking rules live here: a table has to be free, and only one reservation
may hold it at a time. Whether the table *exists* is settled by the write
serializer's queryset, the same way orders validate their menu items.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework import serializers

from core.services import model_update

from .models import Reservation, Table

User = get_user_model()

TABLE_FIELDS = ["number", "label", "is_active"]


@transaction.atomic
def reservation_create(
    *,
    customer: User,
    table: Table,
    party_size: int,
    note: str = "",
) -> Reservation:
    """Reserve ``table`` for ``customer``.

    ``party_size`` is deliberately unbounded above: tables seat as many people
    as the customer asks for. The only rule is that nobody else is holding the
    table.
    """
    try:
        with transaction.atomic():
            return Reservation.objects.create(
                customer=customer,
                table=table,
                party_size=party_size,
                note=note,
            )
    except IntegrityError:
        raise serializers.ValidationError(
            {"table": [f"{table} is already reserved."]}
        )


def reservation_set_status(*, reservation: Reservation, status: str) -> Reservation:
    """Move a reservation to a new status.

    Completing or cancelling releases the table (the partial unique constraint
    only covers active rows), so the next customer can book it.
    """
    if reservation.status == status:
        return reservation

    if not reservation.is_occupying and status == Reservation.Status.ACTIVE:
        raise serializers.ValidationError(
            {"status": ["A finished reservation cannot be made active again."]}
        )

    reservation.status = status
    reservation.save(update_fields=["status", "updated_at"])
    return reservation


def reservation_cancel(*, reservation: Reservation) -> Reservation:
    """Customer-facing cancel, freeing the table."""
    if reservation.status == Reservation.Status.CANCELLED:
        raise serializers.ValidationError(
            {"status": ["This reservation is already cancelled."]}
        )
    if reservation.status == Reservation.Status.COMPLETED:
        raise serializers.ValidationError(
            {"status": ["A completed reservation cannot be cancelled."]}
        )
    return reservation_set_status(
        reservation=reservation, status=Reservation.Status.CANCELLED
    )


def table_create(*, number: int, label: str = "", is_active: bool = True) -> Table:
    return Table.objects.create(number=number, label=label, is_active=is_active)


def table_update(*, table: Table, data: dict[str, Any]) -> Table:
    return model_update(instance=table, fields=TABLE_FIELDS, data=data)


def table_delete(*, table: Table) -> None:
    """Remove a table from the floor plan.

    ``PROTECT`` on the reservation FK means a table with booking history can't
    be deleted; retire it with ``is_active=False`` instead.
    """
    if table.reservations.exists():
        raise serializers.ValidationError(
            {
                "table": [
                    "This table has reservations and cannot be deleted. "
                    "Set is_active to false to retire it instead."
                ]
            }
        )
    table.delete()
