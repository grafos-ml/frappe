"""
Tests for the language package
"""

__author__ = "joaonrb"


from recommendation.filter_owned.filters import FilterOwnedFilter


class DummyUser(object):
    class owned_items:
        @staticmethod
        def all():
            class dummy:
                @staticmethod
                def values_list(dummy_string):
                    return [(1,), (4,)]
            return dummy


class TestFilteredOwned(object):
    """
    Test suit for filter plugin to owned items
    """

    @staticmethod
    def test_owned_items_are_filtered():
        """
        Test if the dummy user items are filtered to minus infinity
        """
        user = DummyUser()
        recommendation = [.4, .2, .7, .1, .3, .4]
        filtered_recommendation = FilterOwnedFilter()(user, recommendation)
        assert filtered_recommendation[0] == float("-inf"), "First item in recommendation is not -inf"
        assert filtered_recommendation[3] == float("-inf"), "Fourth item in recommendation is not -inf"
