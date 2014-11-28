# -*- coding: utf-8 -*-
"""
frappe - frappe.settings.integration
joaonrb, 26 November 2014

Integration test settings
"""

from __future__ import division, absolute_import, print_function
from frappe.settings.base import *

__author__ = "joaonrb"


INSTALLED_APPS = ("django_nose",) + INSTALLED_APPS

TEST_RUNNER = "django_nose.NoseTestSuiteRunner"