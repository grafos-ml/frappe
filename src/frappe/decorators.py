#! -*- encoding: utf-8 -*-

from __future__ import division, absolute_import, print_function
from concurrent.futures import ThreadPoolExecutor as WorkersFactory
from django.core.cache import get_cache
from django.conf import settings
import logging
import functools
import atexit
import itertools
import warnings
try:
    from uwsgi import lock, i_am_the_spooler, unlock
except ImportError:
    warnings.warn("uWSGI lock is not active", RuntimeWarning)
    lock = i_am_the_spooler = unlock = lambda *x: None

__author__ = "joaonrb"

__workerspool__ = WorkersFactory(getattr(settings, "WORKERS", 1))
atexit.register(lambda: __workerspool__.shutdown(False))


class Cached(object):

    def __init__(self, timeout=None, cache="default", lock_id=None):
        self.timeout = timeout
        self.cache = get_cache(cache)
        self.lock_id = lock_id
        self.lock_this = self.no_lock if lock_id is None else self.put_lock

    def __call__(self, function):
        """
        The call of the view.
        """
        @functools.wraps(function)
        def decorated(*args):
            key = "_".join(itertools.chain([function.__name__], map(lambda x: str(x), args)))
            result = self.cache.get(key)
            if result is None:
                return self.reload(key, function(*args))
            return result
        decorated.lock_this = self.lock_this
        decorated.cache = self.cache
        decorated.key = lambda *a: "_".join(itertools.chain([function.__name__], map(lambda x: str(x), a)))
        decorated.timeout = self.timeout
        decorated.set = lambda key, value: self.reload(decorated.key(*key), value)
        return decorated

    def reload(self, key, result):
        self.lock_this(self.cache.set)(key, result, self.timeout)
        return result

    def put_lock(self, function):
        def decorated(*args, **kwargs):
            # ensure the spooler will not call it
            if i_am_the_spooler(self.lock_id):
                return
            lock(self.lock_id)
            try:
                return function(*args, **kwargs)
            finally:
                unlock(self.lock_id)
        return decorated

    def no_lock(self, function):
        def decorated(*args, **kwargs):
            return function(*args, **kwargs)
        return decorated


class ExecuteInBackGround(object):
    """
    Execute work in a background process

    The function must be pickeble. Also a decorated function return a future object instead of the result
    """

    def __init__(self, callable):
        self.__function = callable

    def __call__(self, *args, **kwargs):
            return __workerspool__.submit(self.__function, *args, **kwargs)


class LoadContrib(object):

    def __call__(self):
        from django.conf import settings

        if "frappe.contrib.region" in settings.INSTALLED_APPS:
            from frappe.contrib.region.models import Region, UserRegion
            Region.load_to_cache()
            UserRegion.load_to_cache()
            logging.debug("Regions loaded to cache")

        if "frappe.contrib.diversity" in settings.INSTALLED_APPS:
            from frappe.contrib.diversity.models import Genre, ItemGenre
            Genre.load_to_cache()
            ItemGenre.load_to_cache()
            logging.debug("Genres loaded to cache")

        if "frappe.contrib.logger" in settings.INSTALLED_APPS:
            from frappe.contrib.logger.models import LogEntry
            LogEntry.load_to_cache()
            logging.debug("Logs loaded to cache")