from .base import *

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

CORS_ALLOWED_ORIGINS = []
CORS_ALLOW_CREDENTIALS = False
