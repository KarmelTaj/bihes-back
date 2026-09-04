"""Populate a fresh database with enough data to exercise the API locally.

Creates two accounts (one admin, one customer) and a small menu, so the
frontend has something to render against a brand-new ``db.sqlite3``. Safe to
re-run: every object is looked up before it is created.

    ./.venv/bin/python manage.py seed_demo
"""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.menu.models import Category, MenuItem

User = get_user_model()

DEMO_PASSWORD = "demo12345"

DEMO_USERS = [
    {
        "username": "admin",
        "email": "admin@bihes.local",
        "first_name": "Ada",
        "last_name": "Admin",
        "role": User.Role.ADMIN,
    },
    {
        "username": "customer",
        "email": "customer@bihes.local",
        "first_name": "Cleo",
        "last_name": "Customer",
        "role": User.Role.CUSTOMER,
    },
]

# (category name, category description, [(item name, description, price)])
DEMO_MENU = [
    # (
    #     "Coffee",
    #     "Espresso-based drinks, pulled to order.",
    #     [
    #         ("Royal Latte", "Smooth espresso with steamed milk", "4.99"),
    #         ("Mocha Delight", "Rich chocolate with espresso", "5.49"),
    #         ("Flat White", "Double ristretto under velvet microfoam", "4.59"),
    #         ("Cold Brew", "Steeped eighteen hours, served over ice", "4.25"),
    #     ],
    # ),
    # (
    #     "Pastry",
    #     "Baked in-house every morning.",
    #     [
    #         ("Butter Croissant", "Flaky, buttery and perfectly baked", "3.49"),
    #         ("Almond Danish", "Toasted almonds over frangipane", "3.95"),
    #     ],
    # ),
    # (
    #     "Dessert",
    #     "Something sweet to finish.",
    #     [
    #         ("Chocolate Cake", "Decadent chocolate indulgence", "5.99"),
    #         ("Tiramisu", "Mascarpone, espresso and cocoa", "6.25"),
    #     ],
    # ),
]


class Command(BaseCommand):
    help = "Seed demo users and menu data for local development."

    @transaction.atomic
    def handle(self, *args, **options):
        for spec in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=spec["username"], defaults=spec
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save(update_fields=["password"])
                self.stdout.write(
                    f"  + user {user.username} ({user.role}) / {DEMO_PASSWORD}"
                )
            else:
                self.stdout.write(f"  = user {user.username} already exists")

        for name, description, items in DEMO_MENU:
            category, created = Category.objects.get_or_create(
                name=name, defaults={"description": description}
            )
            self.stdout.write(f"  {'+' if created else '='} category {category.name}")

            for item_name, item_description, price in items:
                _, created = MenuItem.objects.get_or_create(
                    category=category,
                    name=item_name,
                    defaults={
                        "description": item_description,
                        "price": Decimal(price),
                    },
                )
                self.stdout.write(
                    f"    {'+' if created else '='} {item_name} ({price})"
                )

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
