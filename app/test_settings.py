"""Test settings: SQLite, no external services required."""

from pathlib import Path

from app.settings import *  # noqa: F401,F403

BASE_DIR = Path(__file__).resolve().parent

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test.db',
    }
}

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
