# -*- encoding=utf=8 -*-
"""
The filters for the locale functionality
"""

from __future__ import division, absolute_import, print_function
import numpy as np
from itertools import chain
from recommendation.language.models import Locale, Region

__author__ = "joaonrb"


class SimpleLocaleFilter(object):
    """
    A locale filter.
    Fetch the locale of the user and put every item in the recommendation that is not from that locale to the end.
    User can have multiple locales.
    """

    def __call__(self, user, early_recommendation, size=None, **kwargs):
        """
        Call the filter
        """
        unsupported_langs = Locale.get_user_locales(user.pk).symmetric_difference(Locale.get_all_locales())
        #print list(Locale.items_by_locale[l] for l in unsupported_langs)
        unsupported_items = set(chain(*(Locale.get_items_by_locale(l) for l in unsupported_langs)))
        for item in unsupported_items:
            if not any(x in Locale.get_item_locales(item) for x in Locale.get_user_locales(user.pk)):
                early_recommendation[item-1] = -1000
        return early_recommendation


class SimpleRegionFilter(object):
    """
    A locale filter.
    Fetch the locale of the user and put every item in the recommendation that is not from that locale to the end.
    User can have multiple locales.
    """

    def __call__(self, user, early_recommendation, size=None, **kwargs):
        """
        Call the filter
        """
        user_regions = tuple([Region.get_item_list_by_region(region) for region in Region.get_user_regions(user.pk)])
        if len(user_regions) > 0:
            for item_id, score in enumerate(np.sum(user_regions, axis=0), start=1):
                if score == 0:
                    try:
                        early_recommendation[item_id-1] = -1000
                    except IndexError:
                        pass
        return early_recommendation
