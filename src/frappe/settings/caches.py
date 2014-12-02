#! -*- coding: utf-8 -*-
"""
frappe - recommendation.settings
joaonrb, 26 November 2014

Cache Settings
"""

from __future__ import division, absolute_import, print_function

__author__ = "joaonrb"


LOCAL = {
    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    "LOCATION": "django_default_cache",
    "OPTIONS": {
        "MAX_ENTRIES": 10000000,
    }
}

OWNED_ITEMS = {
    "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
    "LOCATION": "127.0.0.1:11211",
}

MODULE = {
    "BACKEND": "frappe.cache.backends.LocMemNoPickleCache",
    "KEY_PREFIX": "frappe_module",
    "TIMEOUT": 30*60
}