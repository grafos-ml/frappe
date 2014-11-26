# -*- coding: utf-8 -*-
"""
frappe - recommendation.settings
joaonrb, 26 November 2014

Django base recommendation.settings for frappe project.

For the full list of recommendation.settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/recommendation.settings/
"""

from __future__ import division, absolute_import, print_function
from settings import databases, caches, logs
from settings.contingency import CONTINGENCY_ITEMS

__author__ = "joaonrb"


SECRET_KEY = "v_7*)d&6w-td^-_)b!w*gd(aflalbzjcbu)4%hqh4$zrp4y_&o"

DEBUG = False

TEMPLATE_DEBUG = False

ALLOWED_HOSTS = ["*"]


# Applications

INSTALLED_APPS = (
    "corsheaders",
    "health_check",
    "health_check_db",
    "health_check_cache",
    "health_check_storage",
    "recommendation",
    "recommendation.api",
    "recommendation.filter_owned",
    "recommendation.language",
    "recommendation.simple_logging",
    "recommendation.diversity",
    "raven.contrib.django",
)


MIDDLEWARE_CLASSES = (
    "corsheaders.middleware.CorsMiddleware"
)


# Allow service in cross domain
CORS_ORIGIN_ALLOW_ALL = True


ROOT_URLCONF = "recommendation.urls"

WSGI_APPLICATION = "recommendation.settings.wsgi.application"


# Database
# https://docs.djangoproject.com/en/1.7/ref/recommendation.settings/#databases

DATABASES = {
    "default": databases.INTEGRATION
}

# Cache
# https://docs.djangoproject.com/en/1.7/ref/recommendation.settings/#caches

CACHES = {
    "default": caches.LOCAL,
    "owned_items": caches.OWNED_ITEMS
}

# Logging
# https://docs.djangoproject.com/en/1.7/ref/recommendation.settings/#logging

LOGGING = logs.LOGGING

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = "en"

TIME_ZONE = "UTC"

USE_I18N = False

USE_L10N = False

USE_TZ = False

# Rest Framework Settings

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ()
}


# Frappe recommendation.settings

RECOMMENDATION_SETTINGS = {
    "default": {
        "core": "recommendation.core.TensorCoFiController",
        "filters": [
            "recommendation.filter_none.filters.FilterNoneItems",
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

# Contingency plan

CONTINGENCY_ITEMS = CONTINGENCY_ITEMS

RESPONSE_TIMEOUT = 1/3