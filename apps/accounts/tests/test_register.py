"""Tests for ``RegisterView`` (POST /accounts/auth/register/)."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.tests.factories import UserFactory

User = get_user_model()


class RegisterApiTests(APITestCase):
    url = reverse("accounts:register")

    def test_register_creates_customer_with_hashed_password(self):
        response = self.client.post(
            self.url,
            {
                "username": "alice",
                "email": "alice@example.com",
                "password": "s3cure-pass-123",
                "first_name": "Alice",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="alice")
        self.assertEqual(user.role, User.Role.CUSTOMER)
        self.assertTrue(user.check_password("s3cure-pass-123"))
        self.assertNotIn("password", response.data)

    def test_register_rejects_duplicate_username(self):
        existing = UserFactory()

        response = self.client.post(
            self.url, {"username": existing.username, "password": "s3cure-pass-123"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data["field_errors"])
