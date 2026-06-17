"""Read-side query logic for the menu app.

Selectors own the querysets (and their select/prefetch optimisations) so the
views never build queries themselves.
"""

from __future__ import annotations

from django.db.models import QuerySet

from .models import Category, MenuItem


def category_list() -> QuerySet[Category]:
    return Category.objects.prefetch_related("items").all()


def menu_item_list() -> QuerySet[MenuItem]:
    return MenuItem.objects.select_related("category").all()
