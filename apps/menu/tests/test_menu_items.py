"""Tests for ``MenuItemViewSet`` (/menu/menu-items/)."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.tests.factories import AdminUserFactory, UserFactory
from apps.menu.tests.factories import CategoryFactory, MenuItemFactory


class MenuItemApiTests(APITestCase):
    list_url = reverse("menu-item-list")

    def setUp(self):
        self.admin = AdminUserFactory()
        self.customer = UserFactory()
        self.category = CategoryFactory(name="Pizza")
        self.item = MenuItemFactory(category=self.category, name="Margherita")

    def test_customer_can_list_and_filter_items(self):
        MenuItemFactory(category=self.category, is_available=False)
        self.client.force_authenticate(self.customer)

        response = self.client.get(self.list_url, {"is_available": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in response.data["results"]]
        self.assertEqual(names, ["Margherita"])

    def test_customer_cannot_update_item(self):
        self.client.force_authenticate(self.customer)
        response = self.client.patch(
            reverse("menu-item-detail", args=[self.item.pk]), {"price": "1.00"}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_and_update_item(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            self.list_url,
            {"category": self.category.pk, "name": "Diavola", "price": "12.00"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["category_name"], "Pizza")

        response = self.client.patch(
            reverse("menu-item-detail", args=[self.item.pk]), {"price": "10.00"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(str(self.item.price), "10.00")
