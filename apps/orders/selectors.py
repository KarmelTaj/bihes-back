"""Read-side query logic for the orders app."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from .models import Order

User = get_user_model()


def order_list(*, user: User) -> QuerySet[Order]:
    """Orders visible to ``user``: admins see everything, customers their own."""
    qs = (
        Order.objects.select_related("customer")
        .prefetch_related("items__menu_item")
        .all()
    )
    if user.is_admin_role:
        return qs
    return qs.filter(customer=user)
