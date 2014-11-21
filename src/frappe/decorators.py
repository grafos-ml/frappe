#! -*- encoding: utf-8 -*-

__author__ = "joaonrb"

from django.core.cache import get_cache
import functools
import itertools
import warnings
try:
    from uwsgi import lock, i_am_the_spooler, unlock
except ImportError:
    warnings.warn("uWSGI lock is not active", RuntimeWarning)
    lock = i_am_the_spooler = unlock = lambda *x: None


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
        decorated.key = "%s_%s" % (function.__name__, "%s")
        decorated.timeout = self.timeout
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