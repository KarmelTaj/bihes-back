"""Model factories for the orders app."""

import factory

from apps.accounts.tests.factories import UserFactory
from apps.menu.tests.factories import MenuItemFactory
from apps.orders.models import Order, OrderItem


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    customer = factory.SubFactory(UserFactory)
    status = Order.Status.PENDING


class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    menu_item = factory.SubFactory(MenuItemFactory)
    quantity = 1
    # Mirrors the service behaviour: the line snapshots the menu item's price.
    unit_price = factory.LazyAttribute(lambda item: item.menu_item.price)
