"""Tests for who can see which reservations (GET /reservations/reservations/)."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.tests.factories import AdminUserFactory, UserFactory
from apps.reservations.tests.factories import ReservationFactory, TableFactory


class ReservationVisibilityApiTests(APITestCase):
    url = reverse("reservation-list")

    def setUp(self):
        self.customer = UserFactory()
        self.mine = ReservationFactory(customer=self.customer, table=TableFactory(number=1))
        self.someone_elses = ReservationFactory(table=TableFactory(number=2))

    def test_customer_sees_only_their_own_reservations(self):
        self.client.force_authenticate(self.customer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([r["id"] for r in response.data["results"]], [self.mine.pk])

    def test_admin_sees_every_reservation(self):
        self.client.force_authenticate(AdminUserFactory())

        response = self.client.get(self.url)

        self.assertEqual(response.data["count"], 2)

    def test_customer_cannot_retrieve_another_customers_reservation(self):
        self.client.force_authenticate(self.customer)

        response = self.client.get(
            reverse("reservation-detail", args=[self.someone_elses.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
