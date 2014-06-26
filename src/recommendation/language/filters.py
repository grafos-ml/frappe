# -*- encoding=utf=8 -*-
"""
The filters for the locale functionality
"""
__author__ = 'joaonrb'

from django.db.models import Q, F
from recommendation.models import Item
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
        supported_locales = user.required_locales.values_list("language_code", flat=True)
        unsupported_items_or_null = Item.objects.exclude(available_locales__language_code=supported_locales)
        unsupported_items = unsupported_items_or_null.exclude(available_locales__isnull=True)
        for item_id, in unsupported_items.values_list("id"):
            early_recommendation[item_id-1] = float("-inf")

        return early_recommendation

