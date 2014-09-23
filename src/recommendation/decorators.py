#! -*- encoding: utf-8 -*-

__author__ = "joaonrb"

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from django.conf import settings
from django.core.cache import get_cache
import functools
import atexit
import itertools
import warnings
import random
import logging
try:
    from uwsgi import lock, i_am_the_spooler, unlock
except ImportError:
    warnings.warn("uWSGI lock is not active", RuntimeWarning)
    lock = i_am_the_spooler = unlock = lambda *x: None

tread_pool = ThreadPoolExecutor(max_workers=getattr(settings, "MAX_THREADS", 2))
clone_pool = ThreadPoolExecutor(max_workers=2)
atexit.register(tread_pool.shutdown)
atexit.register(clone_pool.shutdown)


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


class ContingencyProtocol(object):
    """
    Execute in threading pool
    """
    def __init__(self):
        self.__name__ = "ContingencyProtocol"

    def __call__(self, function):
        """
        The call of the view.
        """

        def decorated(self, user, n=10):
            future = clone_pool.submit(function, self, user, n)
            try:
                result = future.result(getattr(settings, "RESPONSE_TIMEOUT", 150./1000.))
            except TimeoutError:
                future.cancel()
                logging.log(logging.ERROR, "Contingency Protocol delivered")
                result = random.sample(getattr(settings, "CONTINGENCY_ITEMS", SAMPLE), n)
            return result
        return decorated

SAMPLE = ["364927",
          "409126",
          "444796",
          "461045",
          "433320",
          "463886",
          "427484",
          "451558",
          "448292",
          "404161",
          "463259",
          "404517",
          "460697",
          "462122",
          "458348",
          "386137",
          "457808",
          "458731",
          "444510",
          "423716",
          "438392",
          "455256",
          "459110",
          "452888",
          "464181",
          "451792",
          "442754",
          "404159",
          "371236",
          "371377",
          "379491",
          "404807",
          "408212",
          "375680",
          "396642",
          "413346",
          "443840",
          "435200",
          "407950",
          "425224",
          "420136",
          "413558",
          "408420",
          "377829",
          "434270",
          "422606",
          "450780",
          "460939",
          "467211",
          "439916",
          "424192",
          "376961",
          "460165",
          "462823",
          "469183",
          "462581",
          "462106",
          "471349",
          "468167",
          "462667",
          "463861",
          "471937",
          "429582",
          "472581",
          "466734",
          "423452",
          "455484",
          "456176",
          "463884",
          "437194",
          "465814",
          "471309",
          "454308",
          "429748",
          "429662",
          "448332",
          "468839",
          "447408",
          "468737",
          "443078",
          "470467",
          "421962",
          "429592",
          "468322",
          "464136",
          "464130",
          "467426",
          "461514",
          "466518",
          "444220",
          "379989",
          "423062",
          "471037",
          "410220",
          "463184",
          "371030",
          "470513",
          "462702",
          "427878",
          "458466"]