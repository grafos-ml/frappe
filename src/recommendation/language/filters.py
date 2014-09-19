# -*- encoding=utf=8 -*-
"""
The filters for the locale functionality
"""
__author__ = 'joaonrb'

from itertools import chain
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
        unsupported_langs = Locale.get_user_locales(user.pk).symmetric_difference(l for l in Locale.get_all_locales())
        #print list(Locale.items_by_locale[l] for l in unsupported_langs)
        unsupported_items = set(chain(*(Locale.get_items_by_locale(l) for l in unsupported_langs)))

        for item in unsupported_items:
            if not any(x in Locale.get_item_locales(item) for x in Locale.get_user_locales(user.pk)):
                early_recommendation[item-1] = float("-inf")
        return early_recommendation

