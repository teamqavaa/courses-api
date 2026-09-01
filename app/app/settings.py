"""
Django settings for app project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env.local')
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-srb9il*-hdj!v77(^t!-ct$=y202x6zp8ygd)ah*xdrnu(hci@')

# DEBUG = os.getenv('DEBUG', 'False') == 'True'
DEBUG = True

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')

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
    'users',
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

AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'users.backends.EmailOrPhoneBackend',
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:3001',
]

# courses-api issues the JWT. The shared signing value may come from the
# SSO_JWT_SECRET environment variable or a mounted secret file (docker secrets
# style); fall back to SECRET_KEY when neither is present so local dev still
# works without extra configuration.
def _sso_jwt_secret():
    env = os.environ.get('SSO_JWT_SECRET')
    if env:
        return env
    secret_file = '/run/secrets/sso_jwt_secret'
    if os.path.exists(secret_file):
        with open(secret_file) as fh:
            return fh.read().strip()
    return SECRET_KEY

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema'
}


# Configuration SimpleJWT
SIMPLE_JWT = {
    'SIGNING_KEY': _sso_jwt_secret(),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'sub',
}



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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SSO_INTROSPECT_URL = os.getenv('SSO_INTROSPECT_URL')
SSO_CLIENT_ID = os.getenv('SSO_CLIENT_ID')
SSO_CLIENT_SECRET = os.getenv('SSO_CLIENT_SECRET')
