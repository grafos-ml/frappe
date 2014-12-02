# -*- coding: utf-8 -*-
"""
frappe - frappe.settings
joaonrb, 26 November 2014

Django base settings for frappe project.

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

from __future__ import division, absolute_import, print_function
from frappe.settings import databases, caches, logs
from frappe.settings.contingency import CONTINGENCY_ITEMS

__author__ = "joaonrb"


SECRET_KEY = "v_7*)d&6w-td^-_)b!w*gd(aflalbzjcbu)4%hqh4$zrp4y_&o"

DEBUG = False

TEMPLATE_DEBUG = False

ALLOWED_HOSTS = ["*"]


# Applications

INSTALLED_APPS = (
    # Apps for Frappé
    "corsheaders",
    "rest_framework",
    "health_check",
    "health_check_db",
    "health_check_cache",
    "health_check_storage",
    "frappe",
    "frappe.api",
    "frappe.contrib.region",
    "frappe.contrib.logger",
    "frappe.contrib.diversity",
    "raven.contrib.django",
)


MIDDLEWARE_CLASSES = (
    "corsheaders.middleware.CorsMiddleware",
)


# Allow service in cross domain
CORS_ORIGIN_ALLOW_ALL = True


ROOT_URLCONF = "frappe.urls"

WSGI_APPLICATION = "frappe.settings.wsgi.application"


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    "default": databases.INTEGRATION
}

# Cache
# https://docs.djangoproject.com/en/1.7/ref/settings/#caches

CACHES = {
    "default": caches.LOCAL,
    "owned_items": caches.OWNED_ITEMS,
    "module": caches.MODULE
}

# Logging
# https://docs.djangoproject.com/en/1.7/ref/settings/#logging

LOGGING = logs.LOGGING

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = "en"

TIME_ZONE = "UTC"

USE_I18N = False

USE_L10N = False

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = "/static/"

# Rest Framework Settings

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ()
}

# Contingency plan

CONTINGENCY_ITEMS = CONTINGENCY_ITEMS

RESPONSE_TIMEOUT = 1/3