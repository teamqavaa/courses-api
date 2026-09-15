"""
Django settings for app project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# 🟢 Priorité : .env d'abord, puis .env.local par-dessus pour écraser en dev local
load_dotenv(BASE_DIR / '.env')
load_dotenv(BASE_DIR / '.env.local')

# 🟢 Clé secrète : Utilise l'environnement ou la clé de fallback
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-srb9il*-hdj!v77(^t!-ct$=y202x6zp8ygd)ah*xdrnu(hci@')

# 🟢 DEBUG : Evaluation propre du booléen (True par défaut)
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')

# 🟢 ALLOWED_HOSTS : Nettoyage automatique des espaces
ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',') if host.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'corsheaders',
    'drf_spectacular',

    # My apps
    'core',
    'courses_type',
    'categories',
    'courses',
    'modules',
    'lessons',
    'videos',
    'tags',
    'discounts',
    'carts',
    'cart_items',
    'orders',
    'order_items',
    'payments',
    'outcomes',
    'highlights',
    'learning_points',
    'resources',
    'payment_providers',
    'enrollments',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # 🟢 WhiteNoise pour les fichiers statiques
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'

# 🟢 CORS dynamique avec fallback local
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.getenv(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:3000,http://localhost:3001'
    ).split(',') if origin.strip()
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema'
}

# Configuration SimpleJWT
SIMPLE_JWT = {
    'SIGNING_KEY': os.getenv('DJANGO_SECRET_KEY', SECRET_KEY),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'sub',
}

# 🟢 Base de données : Bascule automatique Cloud Run vs Docker Compose
CLOUD_SQL_CONNECTION_NAME = os.getenv('CLOUD_SQL_CONNECTION_NAME')

if CLOUD_SQL_CONNECTION_NAME:
    # Production Cloud Run (Socket Unix)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'contents_lab_db'),
            'USER': os.getenv('DB_USER', 'contents_user'),
            'PASSWORD': os.getenv('DB_PASS', os.getenv('DB_PASSWORD', '')),
            'HOST': f'/cloudsql/{CLOUD_SQL_CONNECTION_NAME}',
        }
    }
else:
    # Développement local Docker Compose
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'HOST': os.getenv('DB_HOST', 'db'),
            'NAME': os.getenv('DB_NAME', 'ssodb'),
            'USER': os.getenv('DB_USER', 'ssouser'),
            'PASSWORD': os.getenv('DB_PASS', ''),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 🟢 Sécurité SSL appliquée EXCLUSIVEMENT en production (Cloud Run)
if CLOUD_SQL_CONNECTION_NAME:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1', 't')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

SSO_INTROSPECT_URL = os.getenv('SSO_INTROSPECT_URL')
SSO_CLIENT_ID = os.getenv('SSO_CLIENT_ID')
SSO_CLIENT_SECRET = os.getenv('SSO_CLIENT_SECRET')
