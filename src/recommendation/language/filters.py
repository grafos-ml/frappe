# -*- encoding=utf=8 -*-
"""
The filters for the locale functionality
"""
__author__ = 'joaonrb'

from recommendation.models import Item


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
        user_languages = (lang for lang, in user.required_locales.all().values_list("language_code"))
        items_not_supported = Item.objects.exclude(available_locales__language_code__in=user_languages)

        # To shorten the processor working time
        valid_items = [i for i, _ in sorted(enumerate(early_recommendation), key=lambda x: x[1], reverse=True)]
        for item_id, in items_not_supported.filter(id__in=valid_items).values_list("id"):
            early_recommendation[item_id-1] = float("-inf")
        return early_recommendation