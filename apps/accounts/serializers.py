"""Serializers for registration, profile, and JWT login.

Serializers here only declare data shapes and field-level validation; object
creation and mutation are delegated to ``accounts.services`` by the views.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Public-facing representation of a user."""

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role")
        read_only_fields = ("id", "role")


class RegisterSerializer(serializers.ModelSerializer):
    """Input shape for self-service customer registration.

    A ModelSerializer so username uniqueness and field constraints come from
    the model; the actual user creation happens in ``services.user_register``.
    """

    # password = serializers.CharField(
    #     write_only=True, validators=[validate_password], style={"input_type": "password"}
    # )
    password = serializers.CharField(
        write_only=True, validators=[], style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "first_name", "last_name")
        read_only_fields = ("id",)


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT login that embeds ``role`` and ``username`` in the token claims."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["username"] = user.username
        return token
