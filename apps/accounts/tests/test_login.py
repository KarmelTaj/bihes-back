"""Tests for ``RoleTokenObtainPairView`` (POST /accounts/auth/login/)."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.tests.factories import DEFAULT_PASSWORD, AdminUserFactory, UserFactory

User = get_user_model()


class LoginApiTests(APITestCase):
    url = reverse("accounts:login")

    def test_login_returns_tokens_with_role_claim(self):
        admin = AdminUserFactory()

        response = self.client.post(
            self.url, {"username": admin.username, "password": DEFAULT_PASSWORD}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", response.data)
        token = AccessToken(response.data["access"])
        self.assertEqual(token["role"], User.Role.ADMIN)
        self.assertEqual(token["username"], admin.username)

    def test_login_rejects_wrong_password(self):
        user = UserFactory()

        response = self.client.post(
            self.url, {"username": user.username, "password": "wrong"}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
