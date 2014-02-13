# -*- coding: utf-8 -*-
"""
.. :py:module: ffos.recommender.rlogging.decorators
    :platform: Unix, Windows
    :synopsis: A decorator to register events into log. Created on Fev 11, 2014

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
"""

__author__ = {
    'name': 'joaonrb',
    'e-mail': 'joaonrb@gmail.com'
}

from ffos.recommender.rlogging.models import RLog
from ffos.recommender.decorators import Decorator
import functools


class ClickApp(Decorator):
    """
    Decorator for view. Every time a user click on a recommendation
    """

    def __call__(self, function):
        """
        The call of the view.
        """
        @functools.wraps(function)
        def decorated(request, *args, **kwargs):
            user_external_id = request.GET["clicker"]
            app_external_id = request.GET["clicked_app"]
            request.go_to = RLog.click(user_external_id, app_external_id)
            return function(request, *args, **kwargs)
        return decorated


class LogRecommendedApps(Decorator):
    """
    Decorator for recommendations
    """

    def __call__(self, function):
        """
        The call of the view.
        """
        @functools.wraps(function)
        def decorated(*args, **kwargs):
            result = function(*args, **kwargs)
            try:
                user = kwargs["user"]
            except KeyError:
                user = args[0]
            RLog.recommended(user, *result)
            return result
        return decorated