# -*- encoding=utf=8 -*-
"""
The filters for the locale functionality
"""
__author__ = 'joaonrb'

from recommendation.models import User, Item


class SimpleLocaleFilter(object):
    """
    A locale filter.
    Fetch the locale of the user and put every item in the recommendation that is not from that locale to the end.
    User can have multiple locales.
    """

    def __call__(self, user, early_recommendation, **kwargs):
        """
        Call the filter

        :param user: The user that want to know what he wants for apps.
        :type user: recommendation.models.User
        :param early_recommendation: A list with recommendation ids in order to be recommended (ranked).
        :type early_recommendation: list.
        :return: A new set of recommendations ready to fill every item need for the user.
        :rtype: A list of items ids(int).
        """
        user_languages = (lang for lang, in user.required_locales.all().values_list("language_code"))
        items_not_supported = Item.objects.filter(available_locales__language_code__not__in=user_languages)
        for item_id, in items_not_supported.values_list("id"):
            early_recommendation[item_id] = float("-inf")
        return early_recommendation