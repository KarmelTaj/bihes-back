"""Write-side business logic for the menu app.

All category / menu-item mutations flow through these services. They take
already-validated data (the serializers handle field validation), so their job
is persistence plus any cross-field business rules that appear later.
"""

from __future__ import annotations

from typing import Any

from core.services import model_update

from .models import Category, MenuItem

CATEGORY_FIELDS = ["name", "description", "is_active"]
MENU_ITEM_FIELDS = [
    "category",
    "name",
    "description",
    "price",
    "is_available",
    "image_url",
]


def category_create(
    *,
    name: str,
    description: str = "",
    is_active: bool = True,
) -> Category:
    return Category.objects.create(
        name=name, description=description, is_active=is_active
    )


def category_update(*, category: Category, data: dict[str, Any]) -> Category:
    return model_update(instance=category, fields=CATEGORY_FIELDS, data=data)


def category_delete(*, category: Category) -> None:
    category.delete()


def menu_item_create(
    *,
    category: Category,
    name: str,
    price,
    description: str = "",
    is_available: bool = True,
    image_url: str = "",
) -> MenuItem:
    return MenuItem.objects.create(
        category=category,
        name=name,
        price=price,
        description=description,
        is_available=is_available,
        image_url=image_url,
    )


def menu_item_update(*, menu_item: MenuItem, data: dict[str, Any]) -> MenuItem:
    return model_update(instance=menu_item, fields=MENU_ITEM_FIELDS, data=data)


def menu_item_delete(*, menu_item: MenuItem) -> None:
    menu_item.delete()
