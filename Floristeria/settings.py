import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Local .env support; Render supplies the same values through its environment.
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None
if load_dotenv:
    load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'local-development-only-not-for-production-key',
)
DEBUG = os.environ.get('DJANGO_DEBUG', 'true').strip().lower() in {'1', 'true', 'yes', 'on'}
if not DEBUG and (
    not os.environ.get('DJANGO_SECRET_KEY')
    or SECRET_KEY.startswith('local-development-only-')
):
    raise ImproperlyConfigured('Define una DJANGO_SECRET_KEY segura en producción.')

ALLOWED_HOSTS = [
    'floristeria-django.onrender.com',
    '127.0.0.1',
    'localhost',
]
ALLOWED_HOSTS.extend(
    host.strip() for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if host.strip()
)
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'usuarios',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Floristeria.urls'
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
                'usuarios.context_processors.carrito_context',
            ],
        },
    },
]
WSGI_APPLICATION = 'Floristeria.wsgi.application'


def database_from_url(database_url):
    parsed = urlparse(database_url)
    if parsed.scheme not in {'postgres', 'postgresql', 'postgresql+psycopg2'}:
        raise ValueError('DATABASE_URL debe usar el esquema postgres:// o postgresql://')
    query = parse_qs(parsed.query)
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': unquote(parsed.path.lstrip('/')),
        'USER': unquote(parsed.username or ''),
        'PASSWORD': unquote(parsed.password or ''),
        'HOST': parsed.hostname or '',
        'PORT': str(parsed.port or 5432),
        'OPTIONS': {'sslmode': query.get('sslmode', ['require'])[0]},
        'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '60')),
        'CONN_HEALTH_CHECKS': True,
    }


DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
DATABASES = (
    {'default': database_from_url(DATABASE_URL)}
    if DATABASE_URL
    else {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
)

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

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', '10'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').strip().lower() in {'1', 'true', 'yes', 'on'}
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'false').strip().lower() in {'1', 'true', 'yes', 'on'}
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', '')
if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ImproperlyConfigured('EMAIL_USE_TLS y EMAIL_USE_SSL no pueden estar activos a la vez.')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
