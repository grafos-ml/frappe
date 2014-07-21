#! -*- encoding: utf-8 -*-

__author__ = "joaonrb"

from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
import functools

tread_pool = ThreadPoolExecutor(max_workers=settings.MAX_THREADS)


def close():
    tread_pool.shutdown()

import atexit
atexit.register(close)


class PutInThreadQueue(object):
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
    Don't log
    """
    def __call__(self, function):
        @functools.wraps(function)
        def decorated(*args, **kwargs):
            return function(*args, **kwargs)
        return decorated