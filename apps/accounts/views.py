"""Auth endpoints: registration, current-user profile, JWT login.

Views stay thin: serializers validate the input shape, then the views hand
the validated data to ``accounts.services``.
"""

from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    RegisterSerializer,
    RoleTokenObtainPairSerializer,
    UserSerializer,
)
from .services import user_profile_update, user_register


class RegisterView(generics.CreateAPIView):
    """Open endpoint for customers to create an account."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        serializer.instance = user_register(**serializer.validated_data)


class MeView(generics.RetrieveUpdateAPIView):
    """Return / update the authenticated user's own profile."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        serializer.instance = user_profile_update(
            user=serializer.instance, data=serializer.validated_data
        )


class RoleTokenObtainPairView(TokenObtainPairView):
    """JWT login returning access/refresh tokens with role claims."""

    serializer_class = RoleTokenObtainPairSerializer
