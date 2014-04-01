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
import sys
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "(b*v9gk(w^p*%qn1lk2+h7bjg7=(arvy=xu06ahjl9&&@_(_j1"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ["10.22.113.20"]


# Application definition

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    #"django_nose",
    #"debug_toolbar",
    "rest_framework",
    "templatetag_handlebars",
    "recommendation",
    "recommendation.records",
    "recommendation.diversity",
    "recommendation.language",
    "recommendation.api",
    "firefox",
    "firefox.api",
    "firefox.gui",
    "corsheaders"
)

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    #"django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.transaction.TransactionMiddleware",
    "django.middleware.cache.UpdateCacheMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    #"django.middleware.cache.FetchFromCacheMiddleware",
    #"debug_toolbar.middleware.DebugToolbarMiddleware",
)

ROOT_URLCONF = "firefox.urls"

WSGI_APPLICATION = "firefox.wsgi.application"


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases



DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "recommender_v12",
        "USER": "alpha2",
        "PASSWORD": "pasteldenata"
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = "en-en"

TIME_ZONE = "Europe/Madrid"

USE_I18N = True

USE_L10N = True

USE_TZ = True


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
DEBUG_TOOLBAR_PATCH_SETTINGS = False

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
            "MAX_ENTRIES": 1000
        },
    }
}

# Settings for the recommendation

RECOMMENDATION_SETTINGS = {
    "default": {
        "core": ("recommendation.core", "Recommender"),
        "filters": [
            ("recommendation.filter_owned.filters", "FilterOwnedFilter"),
            ("recommendation.language.filters", "SimpleLocaleFilter"),
        ],
        "rerankers": [
            # The order witch the re-rankers or filters are setted here represent the order that they are called
            ("recommendation.records.rerankers", "SimpleLogReRanker"),
            ("recommendation.diversity.rerankers", "DiversityReRanker")
        ]
    }
}

CORS_ORIGIN_ALLOW_ALL = True