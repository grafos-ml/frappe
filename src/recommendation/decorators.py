#! -*- encoding: utf-8 -*-

__author__ = "joaonrb"

from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
import functools
import atexit
import itertools
from django.core.cache import get_cache
try:
    from uwsgi import lock, unlock
except Exception:
    lock = unlock = lambda: None


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


class FromCache(object):

    def __init__(self, timeout=None, cache="default"):
        self.timeout = timeout
        self.cache = get_cache(cache)

    def __call__(self, function):
        """
        The call of the view.
        """
        @functools.wraps(function)
        def decorated(*args, **kwargs):
            lock()
            try:
                key = "_".join(itertools.chain([function.__name__], args,
                                               (("%s:%s" % (k, hash(v))) for k, v in kwargs.items())))
                return self.cache.get(key) or self.reload(key, function(*args, **kwargs))
            finally:
                unlock()
        return decorated

    def reload(self, key, result):
        self.cache.set(key, result, self.timeout)