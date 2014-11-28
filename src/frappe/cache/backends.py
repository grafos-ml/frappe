# -*- coding: utf-8 -*-
"""
frappe - frappe.cache
joaonrb, 28 November 2014

https://djangosnippets.org/snippets/2396/
"""

from __future__ import division, absolute_import, print_function
import time
from django.core.cache.backends.base import BaseCache
from django.utils.synch import RWLock

__author__ = "joaonrb"


# Global in-memory store of cache data. Keyed by name, to provide
# multiple named local memory caches.
_caches = {}
_expire_info = {}
_locks = {}


class LocMemNoPickleCache(BaseCache):
    def __init__(self, name, params):
        BaseCache.__init__(self, params)
        global _caches, _expire_info, _locks
        self._cache = _caches.setdefault(name, {})
        self._expire_info = _expire_info.setdefault(name, {})
        self._lock = _locks.setdefault(name, RWLock())

    def add(self, key, value, timeout=None, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        self._lock.writer_enters()
        try:
            exp = self._expire_info.get(key)
            if exp is None or exp <= time.time():
                self._set(key, value, timeout)
                return True
            return False
        finally:
            self._lock.writer_leaves()

    def get(self, key, default=None, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        self._lock.reader_enters()
        try:
            exp = self._expire_info.get(key)
            if exp is None:
                return default
            elif exp > time.time():
                return self._cache[key]
        finally:
            self._lock.reader_leaves()
        self._lock.writer_enters()
        try:
            try:
                del self._cache[key]
                del self._expire_info[key]
            except KeyError:
                pass
            return default
        finally:
            self._lock.writer_leaves()

    def _set(self, key, value, timeout=None):
        if len(self._cache) >= self._max_entries:
            self._cull()
        if timeout is None:
            timeout = self.default_timeout
        self._cache[key] = value
        self._expire_info[key] = time.time() + timeout

    def set(self, key, value, timeout=None, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        self._lock.writer_enters()
        # Python 2.4 doesn't allow combined try-except-finally blocks.
        try:
            self._set(key, value, timeout)
        finally:
            self._lock.writer_leaves()

    def has_key(self, key, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        self._lock.reader_enters()
        try:
            exp = self._expire_info.get(key)
            if exp is None:
                return False
            elif exp > time.time():
                return True
        finally:
            self._lock.reader_leaves()

        self._lock.writer_enters()
        try:
            try:
                del self._cache[key]
                del self._expire_info[key]
            except KeyError:
                pass
            return False
        finally:
            self._lock.writer_leaves()

    def _cull(self):
        if self._cull_frequency == 0:
            self.clear()
        else:
            doomed = [k for (i, k) in enumerate(self._cache) if i % self._cull_frequency == 0]
            for k in doomed:
                self._delete(k)

    def _delete(self, key):
        try:
            del self._cache[key]
        except KeyError:
            pass
        try:
            del self._expire_info[key]
        except KeyError:
            pass

    def delete(self, key, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        self._lock.writer_enters()
        try:
            self._delete(key)
        finally:
            self._lock.writer_leaves()

    def clear(self):
        self._cache.clear()
        self._expire_info.clear()


# For backwards compatibility
class CacheClass(LocMemNoPickleCache):
    pass