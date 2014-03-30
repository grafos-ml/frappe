# -*- encoding: utf-8 -*-
"""
Test package for the diversification in general.
"""

__author__ = 'joaonrb'

from recommendation.diversity.rerankers import BinomialDiversity, TurboBinomialDiversity
from recommendation.models import User
from recommendation.core import Recommender


class DummyDiversity(BinomialDiversity):
    """
    Implementation of a dummy Diversity algorithm for test purposes
    """

    A = "a"
    B = "b"
    C = "c"

    P_A = 0.5
    P_B = 0.25
    P_C = 0.25

    def __init__(self, lambda_constant=0.5):
        """
        Constructor

        :param lambda_constant: Lambda constant. Must be between 0 and 1.
        :type lambda_constant: float
        """
        constant = 100
        i0 = 0
        genres = [(i, self.A) for i in range(i0, i0+int(constant*self.P_A))]

        i0 += int(constant*self.P_A)
        genres += [(i, self.B) for i in range(i0, i0+int(constant*self.P_B))]

        i0 += int(constant*self.P_B)
        genres += [(i, self.C) for i in range(i0, i0+int(constant*self.P_C))]

        assert len(genres) == constant, "Categories does not have %d elements" % constant

        self.genre_by_item = {}
        self.genres = {}
        for item_id, genre in genres:
            self.genres[genre] = self.genres.get(genre, 0.) + 1.
            try:
                self.genre_by_item[item_id].append(genre)
            except KeyError:
                self.genre_by_item[item_id] = [genre]
        self.number_items = constant
        self.recommendation_size = 2
        self.lambda_constant = lambda_constant


class TurboDummy(TurboBinomialDiversity):
    """
    Implementation of a dummy Diversity algorithm for test purposes
    """

    A = "a"
    B = "b"
    C = "c"

    P_A = 0.5
    P_B = 0.25
    P_C = 0.25

    def __init__(self, lambda_constant=0.5):
        """
        Constructor

        :param lambda_constant: Lambda constant. Must be between 0 and 1.
        :type lambda_constant: float
        """
        constant = 100
        i0 = 0
        genres = [(i, self.A) for i in range(i0, i0+int(constant*self.P_A))]

        i0 += int(constant*self.P_A)
        genres += [(i, self.B) for i in range(i0, i0+int(constant*self.P_B))]

        i0 += int(constant*self.P_B)
        genres += [(i, self.C) for i in range(i0, i0+int(constant*self.P_C))]

        assert len(genres) == constant, "Categories does not have %d elements" % constant

        self.genre_by_item = {}
        self.genres = {}
        for item_id, genre in genres:
            self.genres[genre] = self.genres.get(genre, 0.) + 1.
            try:
                self.genre_by_item[item_id].append(genre)
            except KeyError:
                self.genre_by_item[item_id] = [genre]
        self.number_items = constant
        self.recommendation_size = 2
        self.lambda_constant = lambda_constant
        self.mapped_results = {
            "P": {}
        }


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
        cls.controller = Recommender()
        cls.user = User.objects.order_by("?")[0]
        cls.original_recommendation = cls.controller.get_app_significance_list(
            user=cls.user, u_matrix=cls.controller.get_user_matrix(), a_matrix=cls.controller.get_apps_matrix())
        cls.original_recommendation_ids = \
            [item_id for item_id, _ in
             sorted(enumerate(cls.original_recommendation.tolist()), key=lambda x: x[1], reverse=True)]
        cls.diversity = BinomialDiversity(cls.original_recommendation_ids, 4)
        cls.dummy_diversity = DummyDiversity()
        cls.turbo_dummy = TurboDummy()

    def test_coverage(self):
        """
        Test the coverage
        """
        cover_0_apps = self.diversity.coverage([])
        assert cover_0_apps == 1., "The coverage for empty lists isn't 1. Value=%f" % cover_0_apps

    def test_coverage_with_dummy(self):
        """
        Test coverage with dummy
        """
        cover_b_a = self.dummy_diversity.coverage([50, 0])  # 50 a "b" item and 0 an "a" item
        assert 0.825481 < cover_b_a < 0.825483, "The coverage [b, a] isn't 0.825482. Value=%f" % cover_b_a
        cover_a_a = self.dummy_diversity.coverage([1, 0])  # 1 a "a" item and 0 an "a" item
        assert 0.681419 < cover_a_a < 0.681421, "The coverage [a, a] isn't 0.681420. Value=%f" % cover_a_a

    def test_non_redundancy_dummy(self):
        """
        Test the non redundancy with a dummy
        """
        non_red_b_a = self.dummy_diversity.non_redundancy([50, 0])  # 50 a "b" item and 0 an "a" item
        assert 1. == non_red_b_a, "The non redundancy [b, a] isn't 1.0. Value=%f" % non_red_b_a
        non_red_a_a = self.dummy_diversity.non_redundancy([1, 0])  # 1 a "a" item and 0 an "a" item
        assert 0.333332 < non_red_a_a < 0.333334, "The non redundancy [a, a] isn't 0.333333. Value=%f" % non_red_a_a

    def test_non_redundancy(self):
        """
        Test the non redundancy
        """
        non_red_0_apps = self.diversity.non_redundancy([])
        assert non_red_0_apps == 1., "The non redundancy for empty lists isn't 1. Value=%f" % non_red_0_apps

    def test_coverage_with_turbo_dummy(self):
        """
        Test coverage with turbo dummy
        """
        self.turbo_dummy.coverage([50])  # Turbo algorithm needs to have information of the element previous
        cover_b_a = self.turbo_dummy.coverage([50, 0])  # 50 a "b" item and 0 an "a" item
        assert 0.825481 < cover_b_a < 0.825483, "The coverage [b, a] isn't 0.825482. Value=%f" % cover_b_a
        self.turbo_dummy.coverage([1])  # Turbo algorithm needs to have information of the element previous
        cover_a_a = self.turbo_dummy.coverage([1, 0])  # 1 a "a" item and 0 an "a" item
        assert 0.681419 < cover_a_a < 0.681421, "The coverage [a, a] isn't 0.681420. Value=%f" % cover_a_a

    def test_non_redundancy_turbo_dummy(self):
        """
        Test the non redundancy with a turbo dummy
        """
        self.turbo_dummy.non_redundancy([50])  # Turbo algorithm needs to have information of the element previous
        non_red_b_a = self.turbo_dummy.non_redundancy([50, 0])  # 50 a "b" item and 0 an "a" item
        assert 1. == non_red_b_a, "The non redundancy [b, a] isn't 1.0. Value=%f" % non_red_b_a
        self.turbo_dummy.non_redundancy([1])  # Turbo algorithm needs to have information of the element previous
        non_red_a_a = self.turbo_dummy.non_redundancy([1, 0])  # 1 a "a" item and 0 an "a" item
        assert 0.333332 < non_red_a_a < 0.333334, "The non redundancy [a, a] isn't 0.333333. Value=%f" % non_red_a_a


