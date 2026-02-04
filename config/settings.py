"""
Django settings for Cargo Platform project.
"""
import os
from pathlib import Path
import environ
from django.templatetags.static import static
from django.urls import reverse_lazy

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False)
)

# Read .env file if it exists
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(str(env_file))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Application definition
INSTALLED_APPS = [
    # Django Unfold must be before django.contrib.admin
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'encrypted_model_fields',
    
    # Local apps
    'apps.accounts',
    'apps.metadata',
    'apps.shipments',
    'apps.bids',
    'apps.api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.accounts.cache_middleware.NoCacheForAuthenticatedMiddleware',  # Prevent caching for authenticated users
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.accounts.middleware.PasswordChangeMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='tvirtebis_platform'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Authentication backends - default Django backend
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ka'  # Georgian
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Use ManifestStaticFilesStorage to add cache-busting hashes to static files
# This prevents browsers from caching old versions of CSS/JS files
if not DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session settings
SESSION_COOKIE_AGE = 1800  # 30 minutes
SESSION_SAVE_EVERY_REQUEST = True  # Reset timer on every request
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Remember me functionality (overrides above when checked)
SESSION_COOKIE_AGE_REMEMBER_ME = 2592000  # 30 days

# Prevent session caching issues
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Login/Logout URLs
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/admin/login/'

# Encryption key for sensitive fields
FIELD_ENCRYPTION_KEY = env('FIELD_ENCRYPTION_KEY', default='')

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.api.authentication.PlatformAPIKeyAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%SZ',
}

# Django Unfold settings
UNFOLD = {
    "SITE_TITLE": "ტვირთების პლატფორმა",
    "SITE_HEADER": "ტვირთების გადაზიდვის პლატფორმა",
    "SITE_URL": None,
    "SITE_SYMBOL": "📦",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "ENVIRONMENT": "apps.accounts.admin.get_environment",
    "DASHBOARD_CALLBACK": "apps.accounts.admin.dashboard_callback",
    "SCRIPTS": [],
    "COLORS": {
        "primary": {
            "50": "239 246 255",
            "100": "219 234 254",
            "200": "191 219 254",
            "300": "147 197 253",
            "400": "96 165 250",
            "500": "59 130 246",
            "600": "37 99 235",
            "700": "29 78 216",
            "800": "30 64 175",
            "900": "30 58 138",
            "950": "23 37 84",
        },
    },
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "ka": "🇬🇪",
            },
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "მთავარი",
                "separator": True,
                "items": [
                    {
                        "title": "დეშბორდი",
                        "icon": "dashboard",
                        "link": "/admin/",
                    },
                ],
            },
            # Admin-only navigation
            {
                "title": "მონაცემთა მართვა",
                "separator": True,
                "items": [
                    {
                        "title": "მომხმარებლები",
                        "icon": "people",
                        "link": "/admin/accounts/user/",
                        "permission": "config.unfold_navigation.is_admin_user",
                    },
                    {
                        "title": "პლათფორმა",
                        "icon": "business",
                        "link": "/admin/bids/platform/",
                        "permission": "config.unfold_navigation.is_admin_user",
                    },
                ],
            },
            {
                "title": "განაცხადები და ბიდები",
                "separator": True,
                "items": [
                    {
                        "title": "განაცხადები",
                        "icon": "local_shipping",
                        "link": "/admin/shipments/shipment/",
                    },
                    {
                        "title": "ახალი განაცხადი",
                        "icon": "add_circle",
                        "link": "/admin/shipments/shipment/add/",
                    },
                    {
                        "title": "ბიდები",
                        "icon": "gavel",
                        "link": "/admin/bids/bid/",
                    },
                ],
            },
            # Configuration section - visible to all users
            {
                "title": "კონფიგურაცია",
                "separator": True,
                "items": [
                    {
                        "title": "ტვირთის ტიპები",
                        "icon": "category",
                        "link": "/admin/metadata/cargotype/",
                    },
                    {
                        "title": "ტრანსპორტის ტიპები",
                        "icon": "local_shipping",
                        "link": "/admin/metadata/transporttype/",
                    },
                    {
                        "title": "მოცულობის ერთეულები",
                        "icon": "straighten",
                        "link": "/admin/metadata/volumeunit/",
                    },
                    {
                        "title": "ვალუტები",
                        "icon": "payments",
                        "link": "/admin/metadata/currency/",
                    },
                ],
            },
        ],
    },
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 0 if DEBUG else 300,  # No caching in development
    }
}

# Cache control settings - prevent aggressive browser caching
if DEBUG:
    # In development, disable caching to prevent stale data issues
    CACHE_MIDDLEWARE_SECONDS = 0
    CACHE_MIDDLEWARE_KEY_PREFIX = ''
    
    # Add no-cache headers for all responses in development
    USE_ETAGS = False

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
