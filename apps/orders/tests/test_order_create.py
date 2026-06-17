"""Tests for ``OrderViewSet.create`` (POST /orders/orders/)."""

from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.tests.factories import UserFactory
from apps.menu.tests.factories import MenuItemFactory
from apps.orders.models import Order


class OrderCreateApiTests(APITestCase):
    url = reverse("order-list")

    def setUp(self):
        self.customer = UserFactory()
        self.client.force_authenticate(self.customer)
        self.pizza = MenuItemFactory(name="Margherita", price=Decimal("9.50"))
        self.soda = MenuItemFactory(name="Soda", price=Decimal("2.50"))

    def test_customer_places_order_with_price_snapshot(self):
        response = self.client.post(
            self.url,
            {
                "note": "No basil",
                "items": [
                    {"menu_item": self.pizza.pk, "quantity": 2},
                    {"menu_item": self.soda.pk, "quantity": 1},
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["customer_username"], self.customer.username)
        self.assertEqual(response.data["status"], Order.Status.PENDING)
        self.assertEqual(response.data["total_price"], "21.50")

        # The unit price is snapshotted: changing the menu price later does
        # not change the existing order's total.
        self.pizza.price = Decimal("99.00")
        self.pizza.save()
        order = Order.objects.get(pk=response.data["id"])
        self.assertEqual(order.total_price, Decimal("21.50"))

    def test_order_with_unavailable_item_is_rejected(self):
        off_menu = MenuItemFactory(is_available=False)

        response = self.client.post(
            self.url,
            {"items": [{"menu_item": off_menu.pk, "quantity": 1}]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", response.data["field_errors"])
        self.assertEqual(Order.objects.count(), 0)

    def test_order_without_items_is_rejected(self):
        response = self.client.post(self.url, {"items": []}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)
