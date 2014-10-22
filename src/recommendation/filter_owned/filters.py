#! -*- encoding: utf-8 -*-
"""
Plugin to remove owned items

"""

__author__ = "joaonrb"


class FilterOwned(object):
    """
    Filter To filter the owned items
    """

    def __call__(self, user, recommendation, size=None, **kwargs):
        """

        :param user: User that requested the recommendation
        :param recommendation: List of scores for each item. The index of the score represents the id of the item in db.
        :param size: The size of the recommendation
        :param kwargs: Extra parameters
        :return:
        """
        for item in user.owned_items.values():
            try:
                recommendation[item.pk-1] = float("-inf")
            except IndexError:
                pass
        return recommendation