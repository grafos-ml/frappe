# -*- coding: utf-8 -*-
"""
Django settings for frappe project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
#import pymysql
#pymysql.install_as_MySQLdb()

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "(b*v9gk(w^p*%qn1lk2+h7bjg7=(arvy=xu06ahjl9&&@_(_j1"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = DEBUG

MAX_THREADS = 2
RESPONSE_TIMEOUT = 200./1000.

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = ([
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
] if DEBUG else []) + [
    "corsheaders",
    "frappe",
    #"recommendation.api",
    #"recommendation.filter_owned",
    #"recommendation.language",
    #"recommendation.simple_logging",
    #"recommendation.diversity"
]

if int(os.environ.get("FRAPPE_TEST", 0)):
    INSTALLED_APPS = [
        "django_nose",
        #"debug_toolbar",
        "django_coverage"
    ] + INSTALLED_APPS

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
    "debug_toolbar.middleware.DebugToolbarMiddleware",
) if DEBUG else (
    "corsheaders.middleware.CorsMiddleware",
    #"django.middleware.common.CommonMiddleware",
)

CORS_ORIGIN_ALLOW_ALL = True

ROOT_URLCONF = "frappe.urls"

WSGI_APPLICATION = "frappe.wsgi.application"


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "ffos",
        "USER": "root",
        "PASSWORD": os.environ.get("FRAPPE_PASSWORD", ""),
        "HOST": os.environ.get("FRAPPE_DB_NAME", "localhost"),
        "TEST_CHARSET": "utf8",
        "TEST_COLLATION": "utf8_general_ci",

    #    "ENGINE": "django.db.backends.sqlite3",
    #    "NAME": "ffos.sqlite3",
    #    "ATOMIC_REQUESTS": True
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = "en-en"

TIME_ZONE = "UTC"

USE_I18N = USE_L10N = False
USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = "/static/"

# Logging

# Testing
# Nose settings

TEST_RUNNER = "django_nose.NoseTestSuiteRunner"
NOSE_ARGS = [
    #"--with-coverage",
    #"--cover-package=recommendation",
    #"--cover-html"
]
#DEBUG_TOOLBAR_PATCH_SETTINGS = False

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    #'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.profiling.ProfilingDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.cache.CacheDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    #'debug_toolbar.panels.logger.LoggingPanel',
)

# Rest Framework Settings

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        #'rest_framework.authentication.BasicAuthentication',
        #'rest_framework.authentication.SessionAuthentication',
    )
}

# Caching

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": "127.0.0.1:11211",
    },
    "local": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "django_default_cache",
        "OPTIONS": {"MAX_ENTRIES": 10000000}
    }
}
