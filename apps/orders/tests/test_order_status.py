"""Tests for ``OrderViewSet.set_status`` (PATCH /orders/orders/{id}/status/)."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.tests.factories import AdminUserFactory, UserFactory
from apps.orders.models import Order
from apps.orders.tests.factories import OrderFactory


class OrderStatusApiTests(APITestCase):
    def setUp(self):
        self.admin = AdminUserFactory()
        self.customer = UserFactory()
        self.order = OrderFactory(customer=self.customer)
        self.url = reverse("order-set-status", args=[self.order.pk])

    def test_admin_can_advance_status(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            self.url, {"status": Order.Status.PREPARING}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PREPARING)

    def test_customer_cannot_change_status(self):
        self.client.force_authenticate(self.customer)
        response = self.client.patch(
            self.url, {"status": Order.Status.PREPARING}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_status_is_rejected(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(self.url, {"status": "teleported"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_status_is_rejected(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data["field_errors"])
