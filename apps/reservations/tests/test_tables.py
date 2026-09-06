"""Tests for ``TableViewSet`` (/reservations/tables/) — the admin floor plan."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.tests.factories import AdminUserFactory, UserFactory
from apps.reservations.models import Table
from apps.reservations.tests.factories import ReservationFactory, TableFactory


class TableApiTests(APITestCase):
    list_url = reverse("table-list")

    def setUp(self):
        self.admin = AdminUserFactory()
        self.customer = UserFactory()
        self.table = TableFactory(number=1)

    def test_admin_adds_a_table_without_a_deploy(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            self.list_url, {"number": 11, "label": "Patio 1"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Table.objects.filter(number=11).exists())

    def test_customer_cannot_reshape_the_floor_plan(self):
        self.client.force_authenticate(self.customer)

        response = self.client.post(self.list_url, {"number": 11}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_table_numbers_are_unique(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(self.list_url, {"number": 1}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retiring_a_table_keeps_its_history(self):
        reservation = ReservationFactory(table=self.table)
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            reverse("table-detail", args=[self.table.pk]),
            {"is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.assertEqual(reservation.table_id, self.table.pk)

    def test_table_with_reservations_cannot_be_deleted(self):
        ReservationFactory(table=self.table)
        self.client.force_authenticate(self.admin)

        response = self.client.delete(reverse("table-detail", args=[self.table.pk]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Table.objects.filter(pk=self.table.pk).exists())

    def test_unused_table_can_be_deleted(self):
        self.client.force_authenticate(self.admin)

        response = self.client.delete(reverse("table-detail", args=[self.table.pk]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
