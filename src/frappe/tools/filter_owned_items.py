#! -*- encoding: utf-8 -*-
"""
Plugin to remove owned items

"""

__author__ = "joaonrb"


class FilterOwnedItems(object):
    """
    Filter To filter the owned items
    """

    def __call__(self, module, user, recommendation, *args, **kwargs):
        """

        :param user: User that requested the recommendation
        :param recommendation: List of scores for each item. The index of the score represents the id of the item in db.
        :param size: The size of the recommendation
        :param kwargs: Extra parameters
        :return:
        """
        for item in user.owned_items.values():
            recommendation[module.items_index[item.external_id]] = -1000
        return recommendation