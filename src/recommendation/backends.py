# -*- coding: utf-8 -*-
"""
Created at Fev 19, 2014

The views for the Recommend API.
"""

from __future__ import division, absolute_import, print_function
from health_check.plugins import BaseHealthCheckBackend
from health_check.backends.base import ServiceUnavailable
from django.core.cache import get_cache
from django.core.cache.backends.base import InvalidCacheBackendError
from django.db import OperationalError
from recommendation.models import Item

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


class CheckDatabaseCacheBackend(BaseHealthCheckBackend):

    def check_status(self):
        try:
            items = Item.objects.all()[0]
            if items != None:
                return True
        except OperationalError:
            raise ServiceUnavailable("Database unavailable")