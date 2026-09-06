"""Read-side query logic for the reservations app.

Selectors own the querysets, including the annotation that decides whether a
table can be booked, so views and services never derive availability
themselves.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, QuerySet

from .models import Reservation, Table

User = get_user_model()


def table_list() -> QuerySet[Table]:
    """Every table, retired ones included — the admin floor-plan view."""
    return Table.objects.all()


def bookable_tables() -> QuerySet[Table]:
    """Tables that exist and haven't been retired."""
    return Table.objects.filter(is_active=True)


def table_availability() -> QuerySet[Table]:
    """Every bookable table, annotated with ``is_available``.

    This is what the booking screen renders: occupied tables are included too,
    so the UI can show them as taken rather than silently hiding them. The
    annotation keeps it to a single query no matter how large the room gets.
    """
    held = Reservation.objects.filter(
        table=OuterRef("pk"), status__in=Reservation.OCCUPYING_STATUSES
    )
    return bookable_tables().annotate(is_available=~Exists(held))


def reservation_list(*, user: User) -> QuerySet[Reservation]:
    """Reservations visible to ``user``: admins see all, customers their own."""
    qs = Reservation.objects.select_related("customer", "table").all()
    if user.is_admin_role:
        return qs
    return qs.filter(customer=user)
