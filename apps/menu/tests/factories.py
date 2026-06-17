"""Model factories for the menu app."""

from decimal import Decimal

import factory

from apps.menu.models import Category, MenuItem


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")
    is_active = True


class MenuItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MenuItem

    category = factory.SubFactory(CategoryFactory)
    name = factory.Sequence(lambda n: f"Item {n}")
    price = Decimal("9.50")
    is_available = True
