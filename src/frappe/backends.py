#! -*- coding: utf-8 -*-
"""
frappe - frappe
joaonrb, 02 December 2014

Documentation TODO
"""

from __future__ import division, absolute_import, print_function
from health_check.plugins import BaseHealthCheckBackend
from health_check.backends.base import ServiceUnavailable
from django.core.cache import get_cache
from django.core.cache.backends.base import InvalidCacheBackendError

__author__ = "joaonrb"


class CheckDefaultCacheBackend(BaseHealthCheckBackend):

    def check_status(self):
        try:
            cache = get_cache("default")
            cache.set("health", True)
            if not cache.get("health"):
                raise ServiceUnavailable("Default Cache not storing values")
            return True
        except InvalidCacheBackendError:
            raise ServiceUnavailable("Default Cache unavailable")


class CheckOwnedItemsCacheBackend(BaseHealthCheckBackend):

    def check_status(self):
        try:
            cache = get_cache("owned_items")
            cache.set("health", True)
            if not cache.get("health"):
                raise ServiceUnavailable("Owned_items Cache not storing values")
            return True
        except InvalidCacheBackendError:
            raise ServiceUnavailable("Owned_items Cache unavailable")