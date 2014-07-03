# -*- encoding=utf=8 -*-
"""
The filters for the locale functionality
"""
__author__ = 'joaonrb'

from recommendation.language.models import Locale


class SimpleLocaleFilter(object):
    """
    A locale filter.
    Fetch the locale of the user and put every item in the recommendation that is not from that locale to the end.
    User can have multiple locales.
    """

    def __call__(self, user, early_recommendation, size=None, **kwargs):
        """
        Call the filter

        :param user: The user that want to know what he wants for apps.
        :type user: recommendation.models.User
        :param early_recommendation: A list with recommendation ids in order to be recommended (ranked).
        :type early_recommendation: list.
        :param size: The size of the recommendation asked
        :return: A new set of recommendations ready to fill every item need for the user.
        :rtype: A list of items ids(int).
        """
        # One SQL query only
        unsupported_items = Locale.get_unsupported_items_by_locale(user)
        for item in unsupported_items:
            early_recommendation[item.id-1] = float("-inf")
        return early_recommendation

