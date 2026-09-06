from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ReservationViewSet, TableAvailabilityView, TableViewSet

router = DefaultRouter()
router.register("reservations", ReservationViewSet, basename="reservation")
router.register("tables", TableViewSet, basename="table")

urlpatterns = [
    path("availability/", TableAvailabilityView.as_view(), name="table-availability"),
] + router.urls
