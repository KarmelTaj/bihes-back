# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

"Bihes's API" — a restaurant ordering REST API built with Django 6 and Django REST Framework. Customers register, browse the menu, and place orders; admins manage the menu and advance order status. There is no frontend in this repo; Swagger UI (served at the site root `/`) is the primary way to explore the API.

## Commands

A virtualenv lives at `./.venv/`. Use it for all commands:

```bash
./.venv/bin/pip install -r requirements.txt   # install dependencies
./.venv/bin/python manage.py runserver        # dev server
./.venv/bin/python manage.py makemigrations   # create migrations
./.venv/bin/python manage.py migrate          # apply migrations
./.venv/bin/python manage.py seed_demo        # demo users + menu for local dev
./.venv/bin/python manage.py test             # run Django tests
./.venv/bin/python manage.py test apps.accounts  # run tests for one app
```

`seed_demo` (in `apps/menu/management/commands/`) is idempotent and creates an
`admin` and a `customer` account, both with password `demo12345`, plus a small
menu — enough for the React frontend to render against a fresh database.

There is no linting config, Makefile, or Docker setup.

**Deployment warning**: pushing to `develop` triggers `.github/workflows/deploy.yml`, which deploys to a live server (self-hosted runner: pip install, migrate, collectstatic, gunicorn restart).

## Settings Architecture

`core/settings/` is a package, not a single file. `core/settings/__init__.py` merges modules in order — later files can override earlier ones:

1. `base.py` — Django core: INSTALLED_APPS, MIDDLEWARE, `AUTH_USER_MODEL = "accounts.User"`, SQLite default database
2. `rest_framework.py` — `REST_FRAMEWORK`, `SIMPLE_JWT` (60-min access / 7-day refresh), `SPECTACULAR_SETTINGS`
3. `logging.py` — structlog + stdlib logging, JSON output to `log/app.log` (rotating)
4. Root-level `local_settings.py` (git-ignored) — loaded last via try/except; holds SECRET_KEY, DEBUG, ALLOWED_HOSTS, and the production PostgreSQL DATABASES. No env-var library (django-environ etc.) is used — per-environment config goes in this file.

When adding a new setting, put it in the matching module; environment-specific values belong in `local_settings.py`.

## Architecture

Three domain apps live under the `apps/` package (registered as `LOCAL_APPS` in `core/settings/base.py`; each AppConfig sets `name = "apps.<app>"` with `label = "<app>"` so app labels, migrations, and `AUTH_USER_MODEL` keep the short name). Imports use the full path (`from apps.accounts...`). They are wired in `core/urls.py` (prefixes: `/accounts/auth/`, `/menu/`, `/orders/`):

- **accounts** — custom `User` (AbstractUser + `role`: ADMIN/CUSTOMER), JWT login via simplejwt (`RoleTokenObtainPairSerializer` embeds role + username in token claims, and accepts an email in the `username` field by resolving it to its owner). Self-registration always creates CUSTOMER role and rejects an email already in use, so that email→username lookup stays unambiguous.
- **menu** — `Category` → `MenuItem` (FK). ModelViewSets via DefaultRouter; **reads are public** (the storefront lists the menu before login), writes are admin-only.
- **orders** — `Order` → `OrderItem`. `OrderItem.unit_price` snapshots `MenuItem.price` at order time, so totals are stable if menu prices change. Order creation validates item availability and runs in an atomic transaction. No delete action. Customers only see their own orders (`get_queryset` filters by user); admins see all. Status changes go through the admin-only `PATCH /orders/{id}/status/` action with a dedicated serializer.

### Cross-cutting conventions

- **Services / selectors layering**: business logic never lives in views or serializers. Each app has a `selectors.py` (read/query logic — owns querysets and their `select_related`/`prefetch_related`) and a `services.py` (write logic — keyword-only functions like `order_create(*, customer, items, note)`). Views call selectors from `get_queryset()` and services from `perform_create`/`perform_update`/`perform_destroy` (or a custom `create`). Serializers only declare shapes and field-level validation; business rules (e.g. item availability) raise `ValidationError` from services. `core/services.py` holds the shared `model_update` helper (saves only changed fields, refreshes `updated_at`).
- **Tests**: each app has a `tests/` package (not a `tests.py`): `factories.py` holds factory_boy factories for that app's models (cross-app factories are imported, e.g. orders uses `apps.accounts.tests.factories.UserFactory`), and each view/action gets its own `test_*.py` file. Tests hit the API with `APITestCase` + `force_authenticate`; use `DEFAULT_PASSWORD` from the accounts factories when a test needs the real login flow.
- **Permissions**: role-based classes live in `apps/accounts/permissions.py` (`IsAdminRole`, `IsAdminOrReadOnly`, `IsOwnerOrAdmin`) and are reused by menu and orders. "Admin" means `User.role == ADMIN`, not Django `is_staff`. DRF default is `IsAuthenticated` + JWT.
- **Serializers**: orders splits read vs. write serializers (`OrderSerializer` vs. `OrderCreateSerializer`/`OrderItemWriteSerializer`) and selects them in `get_serializer_class()` — follow this pattern for asymmetric read/write shapes.
- **Errors**: all API errors flow through `core/api/exceptions.custom_exception_handler`, returning `{request_id, status_code, field_errors, general_errors}`. Don't hand-roll error response shapes in views.
- **Request tracing**: `core/middleware/request_id.py` assigns a UUID per request (or honors `X-Request-ID`), binds it into structlog context, and echoes it in the response header. Use `structlog.get_logger()` so log lines automatically carry the request_id.
- **API docs**: drf-spectacular. Swagger UI at `/`, schema at `/swagger/schema/`, ReDoc at `/swagger/redoc/` (configured in `core/swagger.py`). Assets are served locally via drf-spectacular-sidecar.
