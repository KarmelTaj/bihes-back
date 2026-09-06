"""Model factories for the reservations app."""

import factory

from apps.accounts.tests.factories import UserFactory
from apps.reservations.models import Reservation, Table


class TableFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Table

    number = factory.Sequence(lambda n: n + 1)
    is_active = True


class ReservationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Reservation

    customer = factory.SubFactory(UserFactory)
    # A fresh table per reservation by default, so factory-built bookings don't
    # collide on the constraint that allows one active booking per table.
    table = factory.SubFactory(TableFactory)
    party_size = 2
    status = Reservation.Status.ACTIVE
