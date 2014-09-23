#! -*- encoding: utf-8 -*-

__author__ = "joaonrb"

from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from django.core.cache import get_cache
import functools
import atexit
import itertools
import warnings
try:
    from uwsgidecorators import lock
except ImportError:
    warnings.warn("uWSGI lock is not active", RuntimeWarning)
    lock = lambda x: x


tread_pool = ThreadPoolExecutor(max_workers=getattr(settings, "MAX_THREADS", 2))
atexit.register(tread_pool.shutdown)


class GoToThreadQueue(object):
    """
    Execute in threading pool
    """

    def __call__(self, function):
        """
        The call of the view.
        """
        @functools.wraps(function)
        def decorated(*args, **kwargs):
            result = tread_pool.submit(function, *args, **kwargs)
            return result
            #return function(*args, **kwargs)
        return decorated


class ILogger(object):
    """
    Logger for the recommendation system
    """
    CLICK = 0
    ACQUIRE = 0
    REMOVE = 0
    RECOMMEND = 0

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, function):
        raise NotImplemented


class NoLogger(ILogger):
    """
    Don't do any log
    """
    def __call__(self, function):
        @functools.wraps(function)
        def decorated(*args, **kwargs):
            return function(*args, **kwargs)
        return decorated


class Cached(object):

    def __init__(self, timeout=None, cache="default"):
        self.timeout = timeout
        self.cache = get_cache(cache)

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
        return decorated

    @functools.wraps(lock)
    def reload(self, key, result):
        self.cache.set(key, result, self.timeout)
        return result