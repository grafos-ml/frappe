# -*- coding: utf-8 -*-
"""
Django settings for ffos project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Thread Pool
MAX_THREADS = 4

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "(b*v9gk(w^p*%qn1lk2+h7bjg7=(arvy=xu06ahjl9&&@_(_j1"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ["gabriela"]


# Application definition

INSTALLED_APPS = [
    #"django.contrib.admin",
    #"django.contrib.auth",
    #"django.contrib.contenttypes",
    #"django.contrib.sessions",
    #"django.contrib.messages",
    #"django.contrib.staticfiles",
    #"django_nose",
    #"debug_toolbar",
    #"django_coverage",
    #"rest_framework",
    #"templatetag_handlebars",
    "recommendation",
    "recommendation.records",
    "recommendation.diversity",
    "recommendation.language",
    "recommendation.ab_testing",
    "recommendation.api",
    "firefox",
    "firefox.api",
    "firefox.gui",
]
if DEBUG:
    INSTALLED_APPS += [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django_nose",
        "debug_toolbar",
        "django_coverage",
        "rest_framework",
        "templatetag_handlebars",
    ]

MIDDLEWARE_CLASSES = []
if DEBUG:
    MIDDLEWARE_CLASSES += [
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        #"django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "django.middleware.transaction.TransactionMiddleware",
        "django.middleware.cache.UpdateCacheMiddleware",
        "django.middleware.cache.FetchFromCacheMiddleware",
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        #"recommendation.middleware.NonHtmlDebugToolbarMiddleware",
    ]
ROOT_URLCONF = "firefox.urls"

WSGI_APPLICATION = "firefox.wsgi.application"


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases



DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "recommender_v12",
        "USER": "FFOS",
        "PASSWORD": "pasteldenata",
        #"HOST": "172.16.51.128"
        "HOST": "ana"
    },
    #"default": {
    #    "ENGINE": "django.db.backends.sqlite3",
    #    "NAME": "recommender_v12.db",
    #    'ATOMIC_REQUESTS': True
    #}
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = "en-en"

TIME_ZONE = "Europe/Madrid"

USE_I18N = USE_L10N = USE_TZ = DEBUG


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = "/static/"

# Logging

import logging
from datetime import datetime

FORMAT = "%(asctime)-15s: %(message)s"
path = os.path.dirname(__file__) + "/djangologs/"
if not os.path.exists(path):
    os.makedirs(path)
logging.basicConfig(format=FORMAT, level=logging.DEBUG if DEBUG else logging.WARNING,
                    filename=datetime.now().strftime(path + "%d-%m-%Y %H:%M.log")
                    if DEBUG else datetime.now().strftime(path+"%d-%m-%Y.log"))

# Testing
# Nose settings

TEST_RUNNER = "django_nose.NoseTestSuiteRunner"
#DEBUG_TOOLBAR_PATCH_SETTINGS = False

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    #'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    #'debug_toolbar.panels.profiling.ProfilingDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.cache.CacheDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    #'debug_toolbar.panels.logger.LoggingPanel',
)

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

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
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    } if DEBUG else {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "/var/tmp/django_cache",
        "TIMEOUT": 60,
        "OPTIONS": {
            "MAX_ENTRIES": 100000
        }
        #"BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        #"LOCATION": "unix:/tmp/frappe_models"
    },
    "models": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "/var/tmp/django_models_cache",
        #"BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        #"LOCATION": "unix:/tmp/frappe_models"
    }
}

# Settings for the recommendation

RECOMMENDATION_SETTINGS = {
    "default": {
        #"core": ("recommendation.core", "TensorCoFiRecommender"),
        "core": ("recommendation.ab_testing.rec_controller", "ABTesting"),
        "filters": [
            ("recommendation.filter_owned.filters", "FilterOwnedFilter"),
            ("recommendation.language.filters", "SimpleLocaleFilter"),
        ],
        "rerankers": [
            # The order witch the re-rankers or filters are setted here represent the order that they are called
            #("recommendation.records.rerankers", "SimpleLogReRanker"),
            #("recommendation.diversity.rerankers", "DynamicDiversityReRanker"),
            #("recommendation.diversity.rerankers.diversity_reranker", "DiversityReRanker"),
            ("recommendation.diversity.rerankers.simple", "SimpleDiversityReRanker")
        ]
    }
}

RECOMMENDATION_LOGGER = "recommendation.records.decorators.LogEventInRecords"