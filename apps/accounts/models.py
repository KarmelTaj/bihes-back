"""
Custom user model.

The app distinguishes two kinds of people: **admins**, who manage the menu and
fulfil orders, and **customers**, who place orders. Rather than overloading
Django's ``is_staff`` flag (which also gates access to the Django admin site), we
carry an explicit ``role`` field so the API's notion of "admin" is decoupled from
admin-site access.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        CUSTOMER = "customer", "Customer"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        help_text="Determines API permissions: admins manage the menu and orders.",
    )

    @property
    def is_admin_role(self) -> bool:
        """True for users who can manage the menu and fulfil orders.

        Django superusers are always treated as admins so the bootstrap
        superuser can manage everything without a separate role flip.
        """
        return self.role == self.Role.ADMIN or self.is_superuser
