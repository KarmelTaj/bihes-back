"""Model factories for the accounts app."""

import factory
from django.contrib.auth import get_user_model

User = get_user_model()

# Plaintext password every factory user gets; use it when a test logs in
# through the real auth flow instead of force_authenticate.
DEFAULT_PASSWORD = "s3cure-pass-123"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda user: f"{user.username}@example.com")
    password = factory.django.Password(DEFAULT_PASSWORD)
    role = User.Role.CUSTOMER


class AdminUserFactory(UserFactory):
    username = factory.Sequence(lambda n: f"admin{n}")
    role = User.Role.ADMIN
