from django.contrib import admin

from .models import Reservation, Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("number", "label", "is_active")
    list_filter = ("is_active",)
    search_fields = ("number", "label")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "table", "customer", "party_size", "status", "created_at")
    list_filter = ("status", "table")
    search_fields = ("customer__username", "table__number", "table__label")
