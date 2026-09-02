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

    is_admin = serializers.BooleanField(source="is_admin_role", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role", "is_admin")
        read_only_fields = ("id", "role")


class RegisterSerializer(serializers.ModelSerializer):
    """Input shape for self-service customer registration.

    A ModelSerializer so username uniqueness and field constraints come from
    the model; the actual user creation happens in ``services.user_register``.
    """

    password = serializers.CharField(
        write_only=True, validators=[validate_password], style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "first_name", "last_name")
        read_only_fields = ("id",)

    def validate_email(self, email):
        """Reject an email already in use.

        ``AbstractUser.email`` is not unique at the database level, but login
        accepts an email as the identifier (see
        ``RoleTokenObtainPairSerializer``), so a duplicate would make the
        lookup ambiguous. Enforcing it here keeps that resolution well defined.
        """
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT login that embeds ``role`` and ``username`` in the token claims.

    The identifier field accepts either a username or an email address: the
    frontend login form asks for one input, so an email is resolved to its
    owner's username before simplejwt checks the credentials.
    """

    def validate(self, attrs):
        identifier = attrs.get(self.username_field) or ""
        if "@" in identifier:
            owner = (
                User.objects.filter(email__iexact=identifier).order_by("pk").first()
            )
            if owner is not None:
                attrs[self.username_field] = owner.get_username()
        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["username"] = user.username
        return token
