"""Tests for ``OrderViewSet`` list/retrieve visibility rules."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.tests.factories import AdminUserFactory, UserFactory
from apps.orders.tests.factories import OrderItemFactory


class OrderVisibilityApiTests(APITestCase):
    list_url = reverse("order-list")

    def setUp(self):
        self.admin = AdminUserFactory()
        self.customer = UserFactory()
        self.other_customer = UserFactory()
        self.own_order = OrderItemFactory(order__customer=self.customer).order
        self.detail_url = reverse("order-detail", args=[self.own_order.pk])

    def test_customer_sees_own_orders(self):
        self.client.force_authenticate(self.customer)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.own_order.pk)

    def test_customer_cannot_see_other_customers_orders(self):
        self.client.force_authenticate(self.other_customer)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_sees_all_orders(self):
        OrderItemFactory(order__customer=self.other_customer)
        self.client.force_authenticate(self.admin)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
