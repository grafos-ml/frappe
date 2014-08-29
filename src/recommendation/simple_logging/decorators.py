# -*- coding: utf-8 -*-
"""
A decorator to register events into log. Created on Fev 11, 2014

"""

__author__ = "joaonrb"

from recommendation.simple_logging.models import LogEntry
from recommendation.decorators import ILogger
from recommendation.models import Item
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


class LogEventInRecords(ILogger):
    """
    Log invents into database
    """

    CLICK = Record.CLICK
    ACQUIRE = Record.INSTALL
    REMOVE = Record.REMOVE
    RECOMMEND = Record.RECOMMEND

    def __init__(self, log_type, *args, **kwargs):
        self.log_type = log_type

    def __call__(self, function):
        @functools.wraps(function)
        def decorated(*args, **kwargs):
            user_external_id, item_external_id = args[0], args[1]
            result = function(*args, **kwargs)
            r = Record(user_id=user_external_id, item=Item.objects.get(external_id=item_external_id),
                       type=self.log_type)
            r.save()
            return result
        return decorated