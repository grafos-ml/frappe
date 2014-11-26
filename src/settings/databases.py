# -*- coding: utf-8 -*-
"""
frappe - settings
joaonrb, 26 November 2014

Frappe database settings
"""

from __future__ import division, absolute_import, print_function
import os

__author__ = "joaonrb"


INTEGRATION = {
    "ENGINE": "django.db.backends.mysql",
    "NAME": os.environ.get("FRAPPE_NAME", "ffos"),
    "USER": os.environ.get("FRAPPE_USER", "root"),
    "PASSWORD": os.environ.get("FRAPPE_PASSWORD", ""),
    "HOST": os.environ.get("FRAPPE_HOST", "localhost"),
    "TEST_CHARSET": "utf8",
    "TEST_COLLATION": "utf8_general_ci",
    "ATOMIC_REQUESTS": True
}

UNIT = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": os.path.join(os.path.dirname(os.path.dirname(__file__)), "db.sqlite3"),
}