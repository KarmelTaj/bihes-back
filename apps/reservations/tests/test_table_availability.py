"""Tests for ``TableAvailabilityView`` (GET /reservations/availability/)."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.tests.factories import UserFactory
from apps.reservations.models import Reservation
from apps.reservations.tests.factories import ReservationFactory, TableFactory


class TableAvailabilityApiTests(APITestCase):
    url = reverse("table-availability")

    def setUp(self):
        self.customer = UserFactory()
        self.client.force_authenticate(self.customer)
        self.tables = [TableFactory(number=n) for n in (1, 2, 3)]

    def test_lists_every_bookable_table(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [t["number"] for t in response.data["results"]], [1, 2, 3]
        )
        self.assertTrue(all(t["is_available"] for t in response.data["results"]))

    def test_active_reservation_marks_its_table_unavailable(self):
        ReservationFactory(table=self.tables[1])

        response = self.client.get(self.url)

        by_number = {t["number"]: t["is_available"] for t in response.data["results"]}
        self.assertEqual(by_number, {1: True, 2: False, 3: True})

    def test_finished_reservations_release_their_table(self):
        ReservationFactory(table=self.tables[1], status=Reservation.Status.CANCELLED)
        ReservationFactory(table=self.tables[2], status=Reservation.Status.COMPLETED)

        response = self.client.get(self.url)

        self.assertTrue(all(t["is_available"] for t in response.data["results"]))

    def test_retired_table_is_not_listed(self):
        TableFactory(number=4, is_active=False)

        response = self.client.get(self.url)

        self.assertNotIn(4, [t["number"] for t in response.data["results"]])

    def test_availability_is_a_single_query(self):
        ReservationFactory(table=self.tables[0])

        # One query for the page of tables (plus one for the paginator's count);
        # the annotation must not turn into a per-table lookup.
        with self.assertNumQueries(2):
            self.client.get(self.url)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
