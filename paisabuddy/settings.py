import os
import logging
from pathlib import Path
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-w+rd&5!sy^b^=ytggwj5z70n-q*(!^)r5zpo#w_y48c^6@orf+')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Local apps
    'main',
    
    # Third party apps
    'widget_tweaks',
    'crispy_forms',
    'crispy_bootstrap5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'paisabuddy.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
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

WSGI_APPLICATION = 'paisabuddy.wsgi.application'

# Database configuration
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'))
    )
}

# Custom User Model
AUTH_USER_MODEL = 'main.User'

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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login/Logout URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'

# Messages Framework
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Crispy Forms Configuration
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Session Configuration
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# Security Settings (for production)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Static files compression
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    
    # Database connection pooling
    DATABASES['default']['CONN_MAX_AGE'] = 600

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
if EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
    DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@paisabuddy.com')

# Cache Configuration
REDIS_URL = config('REDIS_URL', default=None)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    } if REDIS_URL else {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'paisabuddy.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'main': {  # Changed from 'core' to 'main' to match your app name
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Application-specific settings
PAISABUDDY_SETTINGS = {
    # Virtual Portfolio Settings
    'INITIAL_VIRTUAL_CASH': 100000.00,
    'MAX_VIRTUAL_CASH': 1000000.00,
    'MIN_TRADE_AMOUNT': 100.00,
    'MAX_TRADE_AMOUNT': 50000.00,
    
    # Gamification Settings
    'POINTS_PER_MODULE': 10,
    'POINTS_PER_QUIZ': 15,
    'POINTS_PER_FRAUD_SCENARIO': 20,
    'POINTS_FOR_DAILY_LOGIN': 5,
    'POINTS_FOR_STREAK_MILESTONE': 25,
    
    # Learning Settings
    'QUIZ_PASSING_SCORE': 70,
    'MAX_QUIZ_ATTEMPTS': 3,
    'STREAK_RESET_HOURS': 48,
    
    # Budget Settings
    'DEFAULT_BUDGET_CATEGORIES': [
        'Food & Dining',
        'Transportation',
        'Shopping',
        'Entertainment',
        'Bills & Utilities',
        'Healthcare',
        'Education',
        'Travel',
        'Other'
    ],
    
    # Fraud Detection Settings
    'FRAUD_SCENARIO_DIFFICULTY_LEVELS': {
        'beginner': 'Basic scam recognition',
        'intermediate': 'Common fraud patterns',
        'advanced': 'Sophisticated scam techniques'
    },
    
    # API Settings
    'STOCK_DATA_REFRESH_INTERVAL': 300,  # 5 minutes
    'PORTFOLIO_UPDATE_INTERVAL': 60,     # 1 minute
    'LEADERBOARD_UPDATE_INTERVAL': 3600, # 1 hour
}

# Development-specific settings
if DEBUG:
    # Django Debug Toolbar
    try:
        import debug_toolbar
        INSTALLED_APPS.append('debug_toolbar')
        MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        INTERNAL_IPS = ['127.0.0.1', '::1']
        DEBUG_TOOLBAR_CONFIG = {
            'DISABLE_PANELS': ['debug_toolbar.panels.redirects.RedirectsPanel'],
            'SHOW_TEMPLATE_CONTEXT': True,
        }
    except ImportError:
        pass
    
    # Dummy email backend for development
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Production-specific settings for Sentry error tracking
if not DEBUG:
    SENTRY_DSN = config('SENTRY_DSN', default=None)
    if SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.django import DjangoIntegration
            from sentry_sdk.integrations.logging import LoggingIntegration
            
            sentry_logging = LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            )
            
            sentry_sdk.init(
                dsn=SENTRY_DSN,
                integrations=[
                    DjangoIntegration(auto_enabling=True),
                    sentry_logging,
                ],
                traces_sample_rate=0.1,
                send_default_pii=True
            )
        except ImportError:
            pass

# Django REST Framework Configuration (if using DRF)
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# Celery Configuration (for background tasks)
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE