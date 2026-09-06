"""Tests for the cancel and admin status actions on a reservation."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.tests.factories import AdminUserFactory, UserFactory
from apps.reservations.models import Reservation
from apps.reservations.tests.factories import ReservationFactory, TableFactory


class ReservationCancelApiTests(APITestCase):
    def setUp(self):
        self.customer = UserFactory()
        self.reservation = ReservationFactory(customer=self.customer, table=TableFactory(number=1))
        self.url = reverse("reservation-cancel", args=[self.reservation.pk])

    def test_owner_cancels_and_frees_the_table(self):
        self.client.force_authenticate(self.customer)

        response = self.client.patch(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Reservation.Status.CANCELLED)
        self.reservation.refresh_from_db()
        self.assertFalse(self.reservation.is_occupying)

    def test_another_customer_cannot_cancel(self):
        self.client.force_authenticate(UserFactory())

        response = self.client.patch(self.url)

        # 404 rather than 403: the queryset is already scoped to the caller's
        # own reservations, so other people's bookings simply don't exist.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, Reservation.Status.ACTIVE)

    def test_admin_can_cancel_any_reservation(self):
        self.client.force_authenticate(AdminUserFactory())

        response = self.client.patch(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cancelling_twice_is_rejected(self):
        self.client.force_authenticate(self.customer)
        self.client.patch(self.url)

        response = self.client.patch(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReservationStatusApiTests(APITestCase):
    def setUp(self):
        self.customer = UserFactory()
        self.reservation = ReservationFactory(customer=self.customer, table=TableFactory(number=1))
        self.url = reverse("reservation-set-status", args=[self.reservation.pk])

    def test_admin_completes_a_reservation(self):
        self.client.force_authenticate(AdminUserFactory())

        response = self.client.patch(
            self.url, {"status": Reservation.Status.COMPLETED}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Reservation.Status.COMPLETED)

    def test_customer_cannot_change_status(self):
        self.client.force_authenticate(self.customer)

        response = self.client.patch(
            self.url, {"status": Reservation.Status.COMPLETED}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_finished_reservation_cannot_be_reactivated(self):
        self.client.force_authenticate(AdminUserFactory())
        self.client.patch(
            self.url, {"status": Reservation.Status.COMPLETED}, format="json"
        )

        response = self.client.patch(
            self.url, {"status": Reservation.Status.ACTIVE}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
