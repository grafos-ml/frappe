# -*- coding: utf-8 -*-
"""
frappe - recommendation.settings.unit
joaonrb, 26 November 2014

Unit test recommendation.settings
"""

from __future__ import division, absolute_import, print_function
from frappe.settings.base import *

__author__ = "joaonrb"

DEBUG = True

TEMPLATE_DEBUG = True

INSTALLED_APPS = (
    # Django apps
    "django.contrib.admin",
    "django.contrib.sites",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_nose",
) + INSTALLED_APPS

MIDDLEWARE_CLASSES += (
    "pyinstrument.middleware.ProfilerMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.SessionAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

DATABASES = {
    "default": databases.UNIT
}

CACHES["owned_items"] = caches.LOCAL

TEST_RUNNER = "django_nose.NoseTestSuiteRunner"