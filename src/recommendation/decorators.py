#! -*- encoding: utf-8 -*-

__author__ = "joaonrb"

from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
import functools
import atexit

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
            tread_pool.submit(function, *args, **kwargs)
            return None
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
