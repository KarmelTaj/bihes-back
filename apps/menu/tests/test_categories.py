"""Tests for ``CategoryViewSet`` (/menu/categories/)."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.tests.factories import AdminUserFactory, UserFactory
from apps.menu.models import Category
from apps.menu.tests.factories import CategoryFactory, MenuItemFactory


class CategoryApiTests(APITestCase):
    list_url = reverse("category-list")

    def setUp(self):
        self.admin = AdminUserFactory()
        self.customer = UserFactory()
        self.category = CategoryFactory(name="Pizza")
        self.item = MenuItemFactory(category=self.category, name="Margherita")

    def test_customer_can_list_categories_with_nested_items(self):
        self.client.force_authenticate(self.customer)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["name"], "Pizza")
        self.assertEqual(
            response.data["results"][0]["items"][0]["name"], "Margherita"
        )

    def test_list_filters_by_is_active(self):
        CategoryFactory(is_active=False)
        self.client.force_authenticate(self.customer)

        response = self.client.get(self.list_url, {"is_active": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [category["name"] for category in response.data["results"]]
        self.assertEqual(names, ["Pizza"])

    def test_customer_cannot_create_category(self):
        self.client.force_authenticate(self.customer)
        response = self.client.post(self.list_url, {"name": "Drinks"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_update_delete_category(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(self.list_url, {"name": "Drinks"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        category_id = response.data["id"]
        detail_url = reverse("category-detail", args=[category_id])

        response = self.client.patch(detail_url, {"is_active": False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Category.objects.get(pk=category_id).is_active)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(pk=category_id).exists())

    def test_anonymous_is_rejected(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
