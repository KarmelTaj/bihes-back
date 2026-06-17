"""Write-side business logic for the accounts app.

Services are the only place users are created or mutated; views and
serializers delegate here so the rules (customer-only self-registration,
which profile fields are editable) live in one spot.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model

from core.services import model_update

User = get_user_model()

# Profile fields a user may change about themselves via the API.
USER_PROFILE_FIELDS = ["username", "email", "first_name", "last_name"]


def user_register(
    *,
    username: str,
    password: str,
    email: str = "",
    first_name: str = "",
    last_name: str = "",
) -> User:
    """Self-service registration.

    Always creates a customer; the admin role is granted out-of-band (Django
    admin or shell) so the public endpoint can't mint privileged accounts.
    """
    user = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=User.Role.CUSTOMER,
    )
    user.set_password(password)
    user.save()
    return user


def user_profile_update(*, user: User, data: dict[str, Any]) -> User:
    """Update the user's own editable profile fields (role is never touched)."""
    return model_update(instance=user, fields=USER_PROFILE_FIELDS, data=data)
