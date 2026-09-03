"""
Django settings for app project.
"""

import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
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
    # Ported from the api_tables feature branch (courses-api / SSO split)
    'requirements',
    'learning_paths',
    'progress',
    'question_types',
    'quiz_types',
    'quizzes',
    'quiz_questions',
    'quiz_options',
    'quiz_attempts',
    'quiz_answers',
    'quiz_results',
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

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:3001',
]

# courses-api only *verifies* SSO-issued JWTs: the SSO backend signs with its
# private key (RS256) and consumers verify with the matching public key. The
# key may come from the SSO_JWT_PUBLIC_KEY env var, a mounted secret file
# (docker secrets style: /run/secrets/sso_jwt_public), or the committed dev
# public key (.sso-jwt-public.pem in the repository root).
def _sso_jwt_public_key():
    env = os.environ.get('SSO_JWT_PUBLIC_KEY')
    if env:
        return env
    secret_file = '/run/secrets/sso_jwt_public'
    if os.path.exists(secret_file):
        with open(secret_file) as fh:
            return fh.read().strip()
    key_path = BASE_DIR.parent / '.sso-jwt-public.pem'
    if key_path.exists():
        return key_path.read_text().strip()
    raise ImproperlyConfigured(
        'SSO_JWT_PUBLIC_KEY env var or a .sso-jwt-public.pem file is required '
        'to verify SSO tokens (RS256).'
    )

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'core.authentication.CustomJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema'
}


# Configuration SimpleJWT (verification only: we never sign in this service)
SIMPLE_JWT = {
    'ALGORITHM': 'RS256',
    'SIGNING_KEY': _sso_jwt_public_key(),
    'VERIFYING_KEY': _sso_jwt_public_key(),
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

MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SSO_INTROSPECT_URL = os.getenv('SSO_INTROSPECT_URL')
SSO_CLIENT_ID = os.getenv('SSO_CLIENT_ID')
SSO_CLIENT_SECRET = os.getenv('SSO_CLIENT_SECRET')
