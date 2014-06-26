# -*- coding: utf-8 -*-
"""
.. :py:module: ffos.recommendation.rlogging.decorators
    :platform: Unix, Windows
    :synopsis: A decorator to register events into log. Created on Fev 11, 2014

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
"""

__author__ = {
    'name': 'joaonrb',
    'e-mail': 'joaonrb@gmail.com'
}

from recommendation.records.models import Record
import functools
from django.conf import settings


class ClickApp(object):
    """
    Decorator for view. Every time a user click on a recommendation
    """

    def __init__(self):
        self.is_this_installed = "recommendation.records" in settings.INSTALLED_APPS

    def __call__(self, function):
        """
        The call of the view.
        """
        @functools.wraps(function)
        def decorated(request, *args, **kwargs):
            if self.is_this_installed:
                user_external_id = request.GET["clicker"]
                app_external_id = request.GET["clicked_app"]
                request.go_to = Record.click_recommended(user_external_id, app_external_id)
            return function(request, *args, **kwargs)
        return decorated


class LogRecommendedApps(object):
    """
    Decorator for recommendations
    """

    def __init__(self):
        self.is_this_installed = "recommendation.records" in settings.INSTALLED_APPS

    def __call__(self, function):
        """
        The call of the view.
        """
        @functools.wraps(function)
        def decorated(*args, **kwargs):
            result = function(*args, **kwargs)
            if self.is_this_installed:
                try:
                    user = kwargs["user"]
                except KeyError:
                    user = args[0]
                Record.recommended(user, *result)
            return result
        return decorated