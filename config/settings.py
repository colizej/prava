"""
PRAVA.be — Django settings
"""

import os
from pathlib import Path
import environ
import sentry_sdk

# ==============================================================================
# PATHS
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# django-environ
env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / '.env')

# ==============================================================================
# CORE
# ==============================================================================

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# ==============================================================================
# APPS
# ==============================================================================

INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.humanize',

    # Third-party
    'axes',

    # Project apps
    'apps.main',
    'apps.accounts',
    'apps.blog',
    'apps.reglementation',
    'apps.examens',
    'apps.dashboard',
    'apps.shop',
    'apps.rewards',
]

# ==============================================================================
# MIDDLEWARE
# ==============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# ==============================================================================
# TEMPLATES
# ==============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.main.context_processors.site_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ==============================================================================
# DATABASE — SQLite3 (Phase 1)
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            # WAL mode: concurrent reads + writes, no "database is locked" errors
            'init_command': 'PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;',
            'timeout': 20,
        },
    }
}

# ==============================================================================
# AUTH
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ==============================================================================
# INTERNATIONALIZATION — FR / NL / RU
# ==============================================================================

LANGUAGE_CODE = env('LANGUAGE_CODE', default='fr')

LANGUAGES = [
    ('fr', 'Français'),
    ('nl', 'Nederlands'),
    ('ru', 'Русский'),
]

TIME_ZONE = 'Europe/Brussels'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# ==============================================================================
# STATIC FILES
# ==============================================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise compression
import sys as _sys
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage'
            if 'test' in _sys.argv
            else 'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
}

# ==============================================================================
# MEDIA FILES
# ==============================================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==============================================================================
# DEFAULT PRIMARY KEY
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# SITE SETTINGS (used by context processor)
# ==============================================================================

SITE_NAME = 'PRAVA.be'
SITE_DESCRIPTION = "Préparation à l'examen théorique du permis de conduire en Belgique"
SITE_URL = env('SITE_URL', default='http://localhost:8000')

# ==============================================================================
# FREEMIUM SETTINGS
# ==============================================================================

FREE_DAILY_QUESTIONS = 20  # Questions par jour pour les utilisateurs gratuits

# ==============================================================================
# MOLLIE PAYMENT
# ==============================================================================

MOLLIE_API_KEY = env('MOLLIE_API_KEY', default='')

# ==============================================================================
# EMAIL — Mailjet SMTP
# ==============================================================================

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'in-v3.mailjet.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = env('MAILJET_API_KEY', default='')
    EMAIL_HOST_PASSWORD = env('MAILJET_SECRET_KEY', default='')

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@prava.be')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
ADMINS = [('PRAVA Admin', env('ADMIN_EMAIL', default='admin@prava.be'))]

# ==============================================================================
# SECURITY — HTTPS headers (production only)
# ==============================================================================

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000        # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# ==============================================================================
# AUTHENTICATION BACKENDS
# ==============================================================================

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # Must be first for lockout to work
    'django.contrib.auth.backends.ModelBackend',
]

# ==============================================================================
# AXES — Brute force & login protection
# ==============================================================================

AXES_FAILURE_LIMIT = 5           # Lock after 5 failed attempts
AXES_COOLOFF_TIME = 1            # Lockout duration: 1 hour
AXES_RESET_ON_SUCCESS = True     # Reset counter after successful login
AXES_VERBOSE = False
# Trust Caddy reverse-proxy X-Forwarded-For header
AXES_IPWARE_PROXY_COUNT = 1
AXES_IPWARE_META_PRECEDENCE_ORDER = ['HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR']

# ==============================================================================
# SENTRY — Error tracking & performance monitoring
# ==============================================================================

SENTRY_DSN = env('SENTRY_DSN', default='')

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        # Captures 100% of transactions in production; lower in high-traffic env
        traces_sample_rate=1.0,
        # Captures 10% of profiling sessions
        profiles_sample_rate=0.1,
        # Don't report errors in DEBUG mode
        environment='development' if DEBUG else 'production',
        send_default_pii=False,  # GDPR: no personal data in payloads
    )

