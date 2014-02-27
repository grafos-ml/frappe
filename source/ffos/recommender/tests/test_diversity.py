# -*- encoding: utf-8 -*-
"""
Test package for the diversification in general.
"""

__author__ = 'joaonrb'

from ffos.recommender.diversification import BinomialDiversity
from ffos.models import FFOSApp, FFOSUser
from ffos.recommender.controller import SimpleController


class TestDiversity(object):
    """
    Test diversity methods.


    """

    diversity = None

    @classmethod
    def setup_class(cls):
        """
        Setup the test for the diversity module
        """
        cls.controller = SimpleController()
        cls.user = FFOSUser.objects.order_by("?")[0]
        cls.original_recommendation = cls.controller.get_app_significance_list(
            user=cls.user, u_matrix=cls.controller.get_user_matrix(), a_matrix=cls.controller.get_apps_matrix())
        cls.original_recommendation_ids = \
            [item_id
             for item_id, _ in sorted(
                enumerate(cls.original_recommendation.tolist()), cmp=lambda x, y: cmp(y[1], x[1]))]
        cls.diversity = BinomialDiversity(cls.original_recommendation_ids, 4)

    def test_coverage(self):
        """
        Test the coverage
        """
        cover_0_apps = self.diversity.coverage([])
        assert cover_0_apps == 0., "The coverage for empty lists isn't 0. Value=%f" % cover_0_apps
        cover_4_apps_with_1_category = self.diversity.coverage([2379, 9, 41, 233])
        assert 0.999010 < cover_4_apps_with_1_category < 0.999012, \
            "The coverage isn't 0.999011. Value=%f" % cover_4_apps_with_1_category

    def test_non_redundancy(self):
        """
        Test the coverage
        """
        non_red_0_apps = self.diversity.non_redundancy([])
        assert non_red_0_apps == 0., "The non redundancy for empty lists isn't 0. Value=%f" % non_red_0_apps
        non_red_4_apps_with_1_category = self.diversity.non_redundancy([2379, 9, 41, 233])
        assert 0.996944 < non_red_4_apps_with_1_category < 0.996946, \
            "The non redundancy isn't 0.996945. Value=%f" % non_red_4_apps_with_1_category

    def test_diversity_plus(self):
        """
        Test the diversity plus.
        Since the normal diversity is made at cost of coverage and non redundancy it became tested by the tests above.
        """
        apps = [app for app, in FFOSApp.objects.all().order_by("?").values_list("id")[:4]]
        assert self.diversity.diversity(apps) == self.diversity.diversity_plus(apps), \
            "Diversity plus result isn't the same as standard diversity"
