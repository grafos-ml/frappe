"""
Django settings for mozzila project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

import pymysql
pymysql.install_as_MySQLdb()
import logging
try:
    from frappe_settings.contingency import CONTINGENCY_ITEMS
except:
    logging.warn("Couldn't import contingency recommendation")
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'qbw)c7!bc9v=17m#_-s4ldo^yuu1unism1iiw124*$&-bi&9vw'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = TEMPLATE_DEBUG = False

TESTING_MODE = False

ALLOWED_HOSTS = ["*"]

RESPONSE_TIMEOUT = 500./1000.

# Application definiton

INSTALLED_APPS = ([
    "django.contrib.admin",
     "django.contrib.auth",
     "django.contrib.contenttypes",
     "django.contrib.sessions",
     "django.contrib.messages",
     "django.contrib.staticfiles",
] if DEBUG else []) + [
    "corsheaders",
    "recommendation",
    "recommendation.api",
    "recommendation.filter_owned",
    "recommendation.language",
    "recommendation.simple_logging",
    "recommendation.diversity"
]

MIDDLEWARE_CLASSES = (
    "pyinstrument.middleware.ProfilerMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.transaction.TransactionMiddleware",
    #"django.middleware.cache.UpdateCacheMiddleware",
    #"django.middleware.cache.FetchFromCacheMiddleware",
    #"debug_toolbar.middleware.DebugToolbarMiddleware",
) if DEBUG else (
    "corsheaders.middleware.CorsMiddleware",
    #"django.middleware.common.CommonMiddleware",
    #"pyinstrument.middleware.ProfilerMiddleware",
)

CORS_ORIGIN_ALLOW_ALL = True

ROOT_URLCONF = 'frappe_settings.urls'

WSGI_APPLICATION = 'frappe_settings.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': "ffos",
        "USER": os.environ.get("FRAPPE_DB_USER_NAME", "root"),
        "PASSWORD": os.environ.get("FRAPPE_PASSWORD", ""),
        "HOST": os.environ.get("FRAPPE_DB_NAME", "localhost")
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = USE_L10N = USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'


CACHES = {
    #"default": {
    #    "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
    #    "LOCATION": os.environ.get("FRAPPE_MEMCACHED", "127.0.0.1:11211"),
    #},
    "local": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "django_default_cache",
        "OPTIONS": {"MAX_ENTRIES": 10000000}
    },
    "owned_items": {
        #"BACKEND": "uwsgicache.UWSGICache",
        #"LOCATION": "owned_items"
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": os.environ.get("FRAPPE_MEMCACHED", "127.0.0.1:11211"),
    }
}
CACHES["default"] = CACHES["local"]
# Settings for the recommendation

RECOMMENDATION_SETTINGS = {
    "default": {
        "core": "recommendation.core.TensorCoFiController",
        "filters": [
            "recommendation.filter_owned.filters.FilterOwned",
            "recommendation.language.filters.SimpleRegionFilter",
            "recommendation.simple_logging.filters.SimpleLogFilter",
        ],
        "rerankers": [
            "recommendation.diversity.rerankers.SimpleDiversityReRanker"
        ]
    },
    "logger": "recommendation.simple_logging.decorators.LogEvent"
}
