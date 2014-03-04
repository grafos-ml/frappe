# -*- coding: utf-8 -*-
"""

Created on Nov 29, 2013


.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>
"""

__author__ = "joaonrb"

from django.core.cache import cache
from recommender.models import Item


class Filter(object):
    """
    An abstract Filter to be implemented with the real thing.
    """

    def __call__(self, user, app_scores, **kwargs):
        """
        The call method that make this class callable.

        :param user: The FFOSUser or the user external_id
        :param app_scores: The list with the apps scores mapped to their app id
        """


class RepetitionFilter(Filter):
    """
    Make the already installed apps with very low scores so they be drag down.
    """

    def __call__(self, user, app_score, **kwargs):
        """
        :param user: The FFOSUser or the user external_id
        :param app_scores: The list with the apps scores mapped to their app id
        """
        for app in user.installed_apps.all():
            app_score[app.pk-1] = float('-inf')
        return app_score


class LocaleFilter(Filter):
    """
    Remove the list scores if the apps doesn't exist in the user language
    """

    @staticmethod
    def get_user_pref(user):
        """
        Calculate the user preferences.

        :param user: User to get the preferences
        :type user: ffos.models.FFOSUser
        :return: A list off apps that are available with the same locale as the user.
        """
        apps = cache.get('USER_LOCALE_%s' % user.external_id)
        if not apps:
            apps = Item.objects.exclude(supported_locales__name=user.locale).distinct()
            cache.set('USER_LOCALE_%s' % user.external_id, apps)
        return apps

    def __call__(self, user, app_score, **kwargs):
        """
        :param user: The FFOSUser or the user external_id
        :param app_scores: The list with the apps scores mapped to their app id
        """
        for app in self.get_user_pref(user):
            app_score[app.pk-1] = float('-inf')
        return app_score