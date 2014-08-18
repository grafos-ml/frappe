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
        for i in user.owned_items:
            early_recommendation[i.id-1] = float("-inf")
        return early_recommendation