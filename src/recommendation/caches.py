# -*- coding: utf-8 -*-
"""
Provide Cache for FireFox OS recommendation webservice

Created on Dec 5, 2013


.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

"""
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from recommendation.models import User
import functools
import sys
if sys.version_info >= (3, 0):
    basestring = unicode = str


class CacheUser(object):
    """
    Allow users to be cached
    """

    USER = 'USER_%s'

    def __call__(self, function):
        """
        The call of the view.
        """
        @functools.wraps(function)
        def decorated(*args, **kwargs):
            u_id = kwargs['user']
            if isinstance(u_id, basestring):
                user = cache.get(CacheUser.USER % u_id)
                if not user:
                    try:
                        user = User.objects.get(external_id=u_id)
                    except Exception:
                        user = User(external_id=u_id)
                        user.save()
                    cache.set(CacheUser.USER % u_id, user)
                kwargs['user'] = user
            return function(*args, **kwargs)
        return decorated


class CacheApp(object):
    """
    Allow apps to be cached
    """

    APP = 'APP_%s'

    def __call__(self, function):
        """
        The call of the view.
        """
        @functools.wraps(function)
        def decorated(*args, **kwargs):
            a_id = kwargs["item"]
            if isinstance(a_id, basestring):
                app = cache.get(CacheApp.App % a_id)
                if not app:
                    app = get_object_or_404(User, external_id=a_id)
                    cache.set(CacheApp.APP % a_id, app)
                kwargs["item"] = app
            return function(*args, **kwargs)
        return decorated


class CacheMatrix(object):
    """
    Cache the matrix so it doesn't have to get it all the time
    """
    NAME = 'MATRIX_%s'

    def __call__(self, function):
        """
        The call of the view.
        """
        @functools.wraps(function)
        def decorated(*args, **kwargs):
            matrix = cache.get(CacheMatrix.NAME % function.__name__)
            if not matrix:
                matrix = function(*args, **kwargs)
                cache.set(CacheMatrix.NAME % function.__name__, matrix)
            return matrix
        return decorated