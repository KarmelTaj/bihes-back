from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


# SECURITY WARNING: keep the secret key secret, and generate your own:
SECRET_KEY = "put-your-own-generated-secret-key-here"

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
STATIC_ROOT = BASE_DIR / "staticfiles"
