# -*- coding: utf-8 -*-
"""
frappe - recommendation.settings.unit
joaonrb, 26 November 2014

Unit test recommendation.settings
"""

from __future__ import division, absolute_import, print_function
from frappe.settings.base import *

__author__ = "joaonrb"


INSTALLED_APPS = ("django_nose",) + INSTALLED_APPS

DATABASES = {
    "default": databases.UNIT
}

CACHES["owned_items"] = caches.LOCAL

TEST_RUNNER = "django_nose.NoseTestSuiteRunner"