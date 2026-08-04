# Bihes's API

A restaurant ordering REST API built with **Django 6** and **Django REST Framework**.
Customers register, browse the menu, and place orders; admins manage the menu and
advance order status.

There is no frontend in this repository — **Swagger UI is served at the site root
(`/`)** and is the primary way to explore the API.

---

## Requirements

| | |
|---|---|
| Python | 3.12+ (developed and tested on 3.14) |
| Django | 6.0.6 (pinned in `requirements.txt`) |
| Database | SQLite by default — nothing to install |

PostgreSQL is optional. `psycopg` is already in `requirements.txt` if you want it.

---

## Local setup

### 1. Clone and enter the project

```bash
git clone <repository-url>
cd bihes-back
```

### 2. Create the virtualenv

The project's tooling and docs assume a virtualenv at `./venv/`, and every command
below calls its interpreter directly (`./venv/bin/python`), so you never have to
remember whether it is activated.

```bash
python3 -m venv venv
```

### 3. Install dependencies

```bash
./venv/bin/pip install -r requirements.txt
```

### 4. Create `local_settings.py` — required

This project has **no `.env` file and no django-environ**. Per-environment
configuration lives in a git-ignored `local_settings.py` at the project root,
which `core/settings/__init__.py` loads last so it can override anything.

`SECRET_KEY` is defined *only* there, so **the project will not start until you
create this file.** Copy the committed template:

```bash
cp local_settings.example.py local_settings.py
```

Then generate your own secret key and paste it in as `SECRET_KEY`:

```bash
./venv/bin/python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

The template's defaults (`DEBUG = True`, `ALLOWED_HOSTS = ["localhost", "127.0.0.1"]`,
SQLite) are ready for local development as-is.

### 5. Create the database

The default database is SQLite at `db.sqlite3` in the project root. It is
git-ignored, so a fresh clone starts empty — applying migrations creates the file:

```bash
./venv/bin/python manage.py migrate
```

### 6. Create an admin user

Two things are worth understanding here, because they are easy to confuse:

- **`role`** (`admin` / `customer`) on the custom `User` model is what the API's
  permission classes check.
- **`is_staff` / `is_superuser`** only govern access to the Django admin site.

A superuser is treated as an API admin regardless of `role` (see
`User.is_admin_role`), so this one command is enough to get full API access:

```bash
./venv/bin/python manage.py createsuperuser
```

Registering through `POST /accounts/auth/register/` **always** creates a
`customer`; role cannot be set through the API. To promote an existing user, use
the Django admin at `/admin/` or the shell:

```bash
./venv/bin/python manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
U.objects.filter(username='someone').update(role=U.Role.ADMIN)
"
```

### 7. Run the dev server

```bash
./venv/bin/python manage.py runserver
```

Open **<http://127.0.0.1:8000/>** for Swagger UI.

> On startup you will see `staticfiles.W004: The directory .../static does not exist`.
> This is a harmless known warning — `STATICFILES_DIRS` points at a `static/`
> directory that is not in the repo. It does not affect `runserver` or the tests.

---

## Running tests

```bash
./venv/bin/python manage.py test              # whole suite (25 tests)
./venv/bin/python manage.py test apps.orders  # one app
```

Tests use `APITestCase` against a throwaway database; your `db.sqlite3` is never
touched. Each app keeps a `tests/` package with `factories.py` (factory_boy) and
one `test_*.py` per view/action.

---

## Trying the API from the command line

Everything except registration and login requires a **JWT bearer token**.

**1. Register a customer**

```bash
curl -X POST http://127.0.0.1:8000/accounts/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "pw12345", "email": "alice@example.com"}'
```

**2. Log in to get tokens**

```bash
curl -X POST http://127.0.0.1:8000/accounts/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "pw12345"}'
```

Returns `{"access": "...", "refresh": "..."}`. The access token carries `role` and
`username` claims and is valid for 60 minutes; the refresh token lasts 7 days.

**3. Call an authenticated endpoint**

```bash
TOKEN="<paste access token>"
curl http://127.0.0.1:8000/accounts/auth/me/ -H "Authorization: Bearer $TOKEN"
```

**4. Place an order** (as a customer, using real menu item IDs)

```bash
curl -X POST http://127.0.0.1:8000/orders/orders/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"note": "no onions", "items": [{"menu_item": 1, "quantity": 2}]}'
```

---

## API endpoints

Note the `/orders/orders/` doubling — the app is mounted at `/orders/` and its
router registers an `orders` prefix.

### Auth — `/accounts/auth/`

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/accounts/auth/register/` | Public | Self-registration (always `customer`) |
| POST | `/accounts/auth/login/` | Public | Obtain access + refresh tokens |
| POST | `/accounts/auth/login/refresh/` | Public | Exchange refresh for a new access token |
| GET / PUT / PATCH | `/accounts/auth/me/` | Authenticated | Read or update your own profile |

### Menu — `/menu/`

Read for any authenticated user, write for admins (`IsAdminOrReadOnly`).

| Method | Path | Access |
|---|---|---|
| GET | `/menu/categories/`, `/menu/categories/{id}/` | Authenticated |
| POST / PUT / PATCH / DELETE | `/menu/categories/`, `/menu/categories/{id}/` | Admin |
| GET | `/menu/menu-items/`, `/menu/menu-items/{id}/` | Authenticated |
| POST / PUT / PATCH / DELETE | `/menu/menu-items/`, `/menu/menu-items/{id}/` | Admin |

Filters: `?is_active=` on categories; `?category=` and `?is_available=` on items.

### Orders — `/orders/`

| Method | Path | Access |
|---|---|---|
| GET | `/orders/orders/` | Customers see only their own; admins see all |
| POST | `/orders/orders/` | Authenticated — place an order |
| GET | `/orders/orders/{id}/` | Owner or admin |
| PATCH | `/orders/orders/{id}/status/` | Admin only |

Order status: `pending` → `preparing` → `ready` → `completed`, or `cancelled`.
There is deliberately **no delete action** for orders.

### Docs and admin

| Path | What |
|---|---|
| `/` | Swagger UI |
| `/swagger/schema/` | OpenAPI schema |
| `/swagger/redoc/` | ReDoc |
| `/admin/` | Django admin site |

---

## Conventions worth knowing before you commit

These are load-bearing patterns in this codebase, not suggestions:

- **Services / selectors layering.** Business logic lives in neither views nor
  serializers. Each app has `selectors.py` (reads — owns querysets and their
  `select_related`/`prefetch_related`) and `services.py` (writes — keyword-only
  functions like `order_create(*, customer, items, note)`). Views call selectors
  from `get_queryset()` and services from `perform_create` / `perform_update` /
  `perform_destroy`. `core/services.py` holds the shared `model_update` helper.
- **Serializers declare shape only** — field-level validation is fine; business
  rules (e.g. item availability) raise `ValidationError` from services.
- **"Admin" means `role == ADMIN`**, not Django `is_staff`. Role-based permission
  classes live in `apps/accounts/permissions.py` (`IsAdminRole`,
  `IsAdminOrReadOnly`, `IsOwnerOrAdmin`) and are reused by menu and orders.
- **Error envelope.** All errors flow through
  `core/api/exceptions.custom_exception_handler` and come back as
  `{request_id, status_code, field_errors, general_errors}`. Don't hand-roll error
  responses in views.
- **Request tracing.** `core/middleware/request_id.py` assigns a UUID per request
  (or honors an incoming `X-Request-ID`), binds it into the structlog context, and
  echoes it in the response header. Use `structlog.get_logger()` and your log
  lines carry the `request_id` automatically. JSON logs are written to
  `log/app.log`.
- **Price snapshots.** `OrderItem.unit_price` copies `MenuItem.price` at order
  time, so totals stay stable when menu prices later change.

There is no linter config, Makefile, or Docker setup in this repo.

---

## Settings layout

`core/settings/` is a package, not a single module. `__init__.py` merges these in
order, and **later files override earlier ones**:

1. `base.py` — Django core: `INSTALLED_APPS`, `MIDDLEWARE`,
   `AUTH_USER_MODEL = "accounts.User"`, the SQLite default database.
2. `rest_framework.py` — `REST_FRAMEWORK` (JWT auth, `IsAuthenticated` default,
   page size 20), `SIMPLE_JWT`, `SPECTACULAR_SETTINGS`.
3. `logging.py` — structlog + stdlib logging, JSON output to `log/app.log`.
4. `local_settings.py` — git-ignored, loaded last in a `try/except ImportError`.

When adding a setting, put it in the module that matches its concern;
environment-specific values go in `local_settings.py`.

---

## Deployment

`.github/workflows/deploy.yml` exists but is **entirely commented out**, so no
deployment currently runs on push. When it was active, pushing to `develop`
triggered a self-hosted runner that pulled, installed requirements, migrated,
ran `collectstatic`, and restarted gunicorn. Re-enable it deliberately — and note
that the target server keeps its own `local_settings.py`, which is never
overwritten by a deploy.
