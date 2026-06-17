"""Tests for ``MeView`` (GET/PATCH /accounts/auth/me/)."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.tests.factories import UserFactory

User = get_user_model()


class MeApiTests(APITestCase):
    url = reverse("accounts:me")

    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(self.user)

    def test_me_returns_own_profile(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["role"], User.Role.CUSTOMER)

    def test_me_updates_profile_but_not_role(self):
        response = self.client.patch(
            self.url, {"first_name": "Alice", "role": User.Role.ADMIN}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alice")
        self.assertEqual(self.user.role, User.Role.CUSTOMER)

    def test_me_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
