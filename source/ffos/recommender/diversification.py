# -*- coding: utf-8 -*-
"""
Created at 25 February 2014

An try for an implementation of the diversification algorithm described in "Coverage, Redundancy and Size-Awareness in
Genre Diversity for Recommender Systems".

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from scipy.stats import binom
from collections import Counter
from itertools import chain
from ffos.models import FFOSAppCategory
from ffos.recommender.filters import ReRanker


def normalize(value, mean_value, var):
    """
    Normalize value by approximate it to a Gauss(0, 1).

    :param value: Value to normalize
    :type value: float
    :param mean_value: The mean value of the "value's" population
    :type mean_value: float
    :param var: The variance of the "value's" population
    :type var: float
    :return: The normalized value
    :rtype: float
    """
    return (value-mean_value)/var


class BinomialDiversity(object):
    """
    Binomial diversity implementation of the paper that is described in the module
    """

    categories_by_item = None
    categories = None
    recommendation_size = None
    number_items = None

    def __init__(self, items, size, lambda_constant=0.5):
        """
        Constructor

        :param items: A list with the items ids
        :type items: list
        :param size: The size of the recommendation
        :type size: int
        :param lambda_constant: Lambda constant. Must be between 0 and 1.
        :type lambda_constant: float
        """
        categories = FFOSAppCategory.objects.filter(apps__id__in=items).values_list("apps__id", "name")
        self.categories_by_item = {}
        self.categories = {}
        for item_id, category in categories:
            self.categories[category] = self.categories.get(category, 0.) + 1.
            try:
                self.categories_by_item[item_id].append(category)
            except KeyError:
                self.categories_by_item[item_id] = [category]
        self.number_items = len(items)
        self.recommendation_size = size
        self.lambda_constant = lambda_constant

    def coverage(self, recommendation):
        """
        This measure the coverage for this recommendation

        :param recommendation: A proposal for recommendation to get the coverage.
        :type recommendation: iterable
        :return: The coverage of the recommendation
        :rtype: float
        """
        recommendation_categories = (self.categories_by_item[item_id] for item_id in recommendation)
        categories_frequency = set(chain(*recommendation_categories))

        for name in categories_frequency:
            p_category_success = self.categories[name]/self.number_items
            probability_of_category = \
                binom.pmf(0, self.recommendation_size, p_category_success) ** (1./self.number_items)
            try:
                result *= probability_of_category
            except NameError:
                result = probability_of_category
        try:
            return result
        except NameError:
            return 0.

    def non_redundancy(self, recommendation):
        """
        This measure the coverage for this recommendation

        :param recommendation: A proposal for recommendation to get the coverage.
        :type recommendation: iterable
        :return: The coverage of the recommendation
        :rtype: float
        """
        recommendation_categories = (self.categories_by_item[item_id] for item_id in recommendation)
        categories_frequency = Counter(chain(*recommendation_categories)).iteritems()

        for name, category_count in categories_frequency:
            p_category_success = self.categories[name]/self.number_items
            p_category_equal = binom.pmf(category_count, self.recommendation_size, p_category_success)
            p_category_bigger_zero = 0
            for i in xrange(1, self.recommendation_size):
                p_category_bigger_zero += binom.pmf(i, self.recommendation_size, p_category_success)
            probability_non_redundancy = (1.-(p_category_equal/p_category_bigger_zero)) ** (1./self.number_items)
            try:
                result *= probability_non_redundancy
            except NameError:
                result = probability_non_redundancy
        try:
            return result
        except NameError:
            return 0.

    def diversity(self, recommendation):
        """
        Check the diversity of this propose of recommendation.

        :param recommendation: Recommendation to evaluate.
        :type recommendation: list
        :return: The diversity measure. The higher the better(high diversity with low redundancy)
        :rtype: float
        """
        return self.coverage(recommendation) * self.non_redundancy(recommendation)

    def diversity_plus(self, recommendation):
        """
        Check the diversity of this propose of recommendation. This version calculates coverage and

        :param recommendation: Recommendation to evaluate.
        :type recommendation: list
        :return: The diversity measure. The higher the better(high diversity with low redundancy)
        :rtype: float
        """
        recommendation_categories = (self.categories_by_item[item_id] for item_id in recommendation)
        categories_frequency = Counter(chain(*recommendation_categories)).iteritems()

        for name, category_count in categories_frequency:
            p_category_success = self.categories[name]/self.number_items
            p_category_equal = binom.pmf(category_count, self.recommendation_size, p_category_success)
            p_category_bigger_zero = 0
            for i in xrange(1, self.recommendation_size):
                p_category_bigger_zero += binom.pmf(i, self.recommendation_size, p_category_success)
            probability_non_redundancy = (1.-(p_category_equal/p_category_bigger_zero)) ** (1./self.number_items)
            probability_of_category = \
                binom.pmf(0, self.recommendation_size, p_category_success) ** (1./self.number_items)
            try:
                m_non_red *= probability_non_redundancy
                m_coverage *= probability_of_category
            except NameError:
                m_non_red = probability_non_redundancy
                m_coverage = probability_of_category
        try:
            return m_coverage * m_non_red
        except NameError:
            return 0.

    def __call__(self, recommendation, item):
        """
        The diversification gain(or loss) by adding item

        :param recommendation: The recommendation existing
        :type recommendation: list
        :param item: An item to add. Or better, it  rank and id in a tuple.
        :type item: tuple
        :return: The difference between the recommendation and the recommendation with the item. High positive is \
        better than low negative.
        :rtype: float
        """
        rank, item_id = item
        # Assuming the ranking has a uniform distribution from 1 to len(recommendation)
        normalized_rank = normalize(rank, 0.5*(1+self.number_items), (1./12)*(self.number_items-1)**2)

        div = self.diversity_plus(recommendation+[item_id]) - self.diversity_plus(recommendation)

        # Assume that the mean is 0 (it have the same probability of improving and of getting worse). The variance of
        # 0.25 is a guess that the improvement never goes beyond imagination(:s)
        normalized_div = normalize(div, 0., 0.25)
        return (1.-self.lambda_constant)*normalized_rank + self.lambda_constant*normalized_div


class DiversityReRanker(ReRanker):
    """
    The greedy re-ranker that build a new recommendation by choosing the max diversity item in the head of the old
     recommendation. It iterates this process until have a new recommendation.
    """

    def __init__(self, lambda_constant=0.5):
        """
        Constructor

        :param lambda_constant: Some weight. It has to be between 0 and 1. Default is 0.5.
        :type lambda_constant: float
        :return:
        """
        self.lambda_constant = lambda_constant

    def __call__(self, user, recommendation, size, *args, **kwargs):
        """

        :param user: The user that want the recommendation
        :type user: FFOSUser
        :param recommendation: The recommendation to re-rank
        :type recommendation: list
        :param size: The size of the recommendation asked
        :type size: int
        :return: The re-ranked recommendation
        :rtype: list
        """
        size_times = 2
        diversity = BinomialDiversity(recommendation, size, self.lambda_constant)
        new_recommendation = []
        recommendation_set = recommendation[:size*size_times]
        for _ in xrange(size):
            div_list = ((item, diversity(new_recommendation, (index, item)))
                        for index, item in enumerate(recommendation_set, start=1))
            chosen_item = max(div_list, key=lambda x: x[1])[0]
            recommendation_set.remove(chosen_item)
            new_recommendation.append(chosen_item)

        result = new_recommendation + recommendation_set + recommendation[size*size_times:]
        assert len(result) == len(recommendation), "The result lost or gained elements"
        return result