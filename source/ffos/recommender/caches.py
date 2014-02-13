# -*- coding: utf-8 -*-
"""
Provide Cache for FireFox OS recommendation webservice

Created on Dec 5, 2013


.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

"""

from django.shortcuts import get_object_or_404
from django.core.cache import cache
from ffos.models import FFOSUser
from ffos.recommender.decorators import Decorator
import functools


class CacheUser(Decorator):
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
                    user = get_object_or_404(FFOSUser.objects.select_related(), external_id=u_id)
                    cache.set(CacheUser.USER % u_id, user)
                kwargs['user'] = user
            return function(*args, **kwargs)
        return decorated


class CacheApp(Decorator):
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
            a_id = kwargs['app']
            if isinstance(a_id, basestring):
                app = cache.get(CacheApp.App % a_id)
                if not app:
                    app = get_object_or_404(FFOSUser, external_id=a_id)
                    cache.set(CacheApp.APP % a_id, app)
                kwargs['app'] = app
            return function(*args, **kwargs)
        return decorated


class CacheMatrix(Decorator):
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