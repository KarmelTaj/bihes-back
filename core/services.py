"""
Shared service-layer helpers.

The project follows a services/selectors architecture: selectors hold read
(query) logic, services hold write (business) logic, and views/serializers stay
thin. App-specific services live in ``<app>/services.py``; this module hosts
the generic building blocks they share.
"""

from __future__ import annotations

from typing import Any

from django.db import models


def model_update(
    *,
    instance: models.Model,
    fields: list[str],
    data: dict[str, Any],
) -> models.Model:
    """Update ``instance`` from ``data``, saving only the fields that changed.

    Only keys listed in ``fields`` are considered, so callers control exactly
    which attributes a given service is allowed to touch. ``auto_now``
    timestamps are refreshed automatically when the model has an
    ``updated_at`` field.
    """
    updated_fields: list[str] = []

    for field in fields:
        if field not in data:
            continue
        if getattr(instance, field) != data[field]:
            setattr(instance, field, data[field])
            updated_fields.append(field)

    if updated_fields:
        model_field_names = {f.name for f in instance._meta.concrete_fields}
        if "updated_at" in model_field_names:
            updated_fields.append("updated_at")
        instance.save(update_fields=updated_fields)

    return instance
