"""Tests for ``ReservationViewSet.create`` (POST /reservations/reservations/)."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.tests.factories import UserFactory
from apps.reservations.models import Reservation
from apps.reservations.tests.factories import ReservationFactory, TableFactory


class ReservationCreateApiTests(APITestCase):
    url = reverse("reservation-list")

    def setUp(self):
        self.customer = UserFactory()
        self.client.force_authenticate(self.customer)
        self.table = TableFactory(number=1, label="Booth by the window")

    def test_customer_reserves_a_free_table(self):
        response = self.client.post(
            self.url,
            {"table": self.table.pk, "party_size": 4, "note": "Anniversary"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["table"], self.table.pk)
        self.assertEqual(response.data["table_number"], 1)
        self.assertEqual(response.data["table_label"], "Booth by the window")
        self.assertEqual(response.data["party_size"], 4)
        self.assertEqual(response.data["status"], Reservation.Status.ACTIVE)
        self.assertEqual(response.data["customer_username"], self.customer.username)

    def test_party_size_is_not_capped(self):
        response = self.client.post(
            self.url, {"table": self.table.pk, "party_size": 500}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["party_size"], 500)

    def test_occupied_table_cannot_be_reserved(self):
        ReservationFactory(table=self.table)

        response = self.client.post(
            self.url, {"table": self.table.pk, "party_size": 2}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("table", response.data["field_errors"])
        self.assertEqual(Reservation.objects.filter(customer=self.customer).count(), 0)

    def test_table_freed_by_cancellation_can_be_reserved_again(self):
        ReservationFactory(table=self.table, status=Reservation.Status.CANCELLED)

        response = self.client.post(
            self.url, {"table": self.table.pk, "party_size": 2}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unknown_table_is_rejected(self):
        response = self.client.post(
            self.url, {"table": 9999, "party_size": 2}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("table", response.data["field_errors"])
        self.assertEqual(Reservation.objects.count(), 0)

    def test_retired_table_cannot_be_reserved(self):
        retired = TableFactory(number=2, is_active=False)

        response = self.client.post(
            self.url, {"table": retired.pk, "party_size": 2}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("table", response.data["field_errors"])
        self.assertEqual(Reservation.objects.count(), 0)

    def test_non_positive_party_size_is_rejected(self):
        response = self.client.post(
            self.url, {"table": self.table.pk, "party_size": 0}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)

        response = self.client.post(
            self.url, {"table": self.table.pk, "party_size": 2}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
