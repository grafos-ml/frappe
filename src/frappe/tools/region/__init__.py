# -*- encoding=utf=8 -*-
"""
The filters for the locale functionality
"""
__author__ = "joaonrb"

import numpy as np
from frappe.tools.region.models import Region


class SimpleRegionFilter(object):
    """
    A locale filter.
    Fetch the locale of the user and put every item in the recommendation that is not from that locale to the end.
    User can have multiple locales.
    """

    def __call__(self, module,  user, recommendation, *args, **kwargs):
        """
        Call the filter
        """
        user_regions = tuple(Region.get_item_list_by_region(module.pk, region)
                             for region in Region.get_user_regions(user.pk))
        if len(user_regions) > 0:
            # Turns a array of boolean to an array of integer with the items with no region connection with -1000
            recommendation += ((np.sum(user_regions, axis=0)-1)*1000)
        return recommendation
