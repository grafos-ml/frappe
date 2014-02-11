# -*- coding: utf-8 -*-
"""
Created on 11 February 2014

A decorator to register events into log

.. moduleauthor:: joaonrb <joaonrb>
"""

__author__ = {
    'name': 'joaonrb',
    'e-mail': 'joaonrb'
}

from ffos.recommender.logs.models import Log


class ClickApp(object):
    """
    Decorator for view. Every time a user click on a recommendation
    """

    def __init__(self, view):
        """
        Constructor for decorator
        """
        self._view = view

    def __call__(self, request, *args, **kwargs):
        """
        The call of the view.
        """
        user_external_id = request.GET["clicker"]
        app_external_id = request.GET["clicked_app"]
        request.go_to = Log.click(user_external_id, app_external_id,
                                  score=request.GET.get("score", 1.))
        return self._view(request, *args, **kwargs)

