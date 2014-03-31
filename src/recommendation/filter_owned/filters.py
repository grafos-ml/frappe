"""
Plugin to remove owned items

"""

__author__ = 'joaonrb'


class FilterOwnedFilter(object):
    """
    Filter To filter the owned items
    """

    def __call__(self, user, early_recommendation, size=None, **kwargs):
        """

        :param user:
        :param early_recommendation:
        :param size:
        :param kwargs:
        :return:
        """
        for iid, in user.owned_items.all().values_list("id"):
            early_recommendation[iid-1] = float("-inf")
        return early_recommendation