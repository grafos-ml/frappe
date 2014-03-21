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
from recommendation.diversity.models import Genre


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

    genre_by_item = None
    genres = None
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
        genres = Genre.objects.filter(items__id__in=items).values_list("items__id", "name")
        self.genre_by_item = {}
        self.genres = {}
        for item_id, genre in genres:
            self.genres[genre] = self.genres.get(genre, 0.) + 1.
            try:
                self.genre_by_item[item_id].append(genre)
            except KeyError:
                self.genre_by_item[item_id] = [genre]
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
        recommendation_genres = (self.genre_by_item[item_id] for item_id in recommendation)
        genres_in_recommendation = set(chain(*recommendation_genres))
        genres_out_recommendation = (genre for genre in self.genres if genre not in genres_in_recommendation)

        for name in genres_out_recommendation:
            p_get_genre = self.genres[name]/self.number_items
            probability_of_genre = binom.pmf(0, len(recommendation), p_get_genre) ** (1./len(self.genres))
            try:
                result *= probability_of_genre
            except NameError:
                result = probability_of_genre
        return locals().get("result", 0.)

    def non_redundancy(self, recommendation):
        """
        This measure the coverage for this recommendation

        :param recommendation: A proposal for recommendation to get the coverage.
        :type recommendation: iterable
        :return: The coverage of the recommendation
        :rtype: float
        """
        recommendation_genres = (self.genre_by_item[item_id] for item_id in recommendation)
        genres_frequency = Counter(chain(*recommendation_genres)).items()

        for name, genre_count in genres_frequency:
            p_get_genre = self.genres[name]/self.number_items
            p_greater_0 = 1 - binom.pmf(0, len(recommendation), p_get_genre)
            p_greater_0_and_greater_k = \
                sum((binom.pmf(i, len(recommendation), p_get_genre)
                    for i in range(genre_count, int(self.genres[name])+1)))
            probability_non_redundancy = (p_greater_0_and_greater_k/p_greater_0) ** (1./len(genres_frequency))
            try:
                result *= probability_non_redundancy
            except NameError:
                result = probability_non_redundancy
        return locals().get("result", 0.)

    def diversity(self, recommendation):
        """
        Check the diversity of this propose of recommendation.

        :param recommendation: Recommendation to evaluate.
        :type recommendation: list
        :return: The diversity measure. The higher the better(high diversity with low redundancy)
        :rtype: float
        """
        return self.coverage(recommendation) * self.non_redundancy(recommendation)

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

        div = self.diversity(recommendation+[item_id]) - self.diversity(recommendation)

        # Assume that the mean is 0 (it have the same probability of improving and of getting worse). The variance of
        # 0.25 is a guess that the improvement never goes beyond imagination(:s)
        normalized_div = normalize(div, 0., 0.25)
        return (1.-self.lambda_constant)*normalized_rank + self.lambda_constant*normalized_div


class DiversityReRanker(object):
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
        size_times = 4
        diversity = TurboBinomialDiversity(recommendation[:size*size_times], size, self.lambda_constant)
        new_recommendation = []
        recommendation_set = recommendation[:size*size_times]
        for _ in range(size):
            div_list = ((item, diversity(new_recommendation, (index, item)))
                        for index, item in enumerate(recommendation_set, start=1))
            chosen_item = max(div_list, key=lambda x: x[1])[0]
            recommendation_set.remove(chosen_item)
            new_recommendation.append(chosen_item)

        result = new_recommendation + recommendation_set + recommendation[size*size_times:]
        assert len(result) == len(recommendation), "The result lost or gained elements"
        return result


class TurboBinomialDiversity(BinomialDiversity):
    """
    Implementation of BinomialDiversity with improvement by reducing the redundancy calculations. This will be done by
    mapping the tree of results and using this trees in the calculations.
    """

    mapped_results = None

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
        super(TurboBinomialDiversity, self).__init__(items, size, lambda_constant)
        self.mapped_results = {
            "P": {}
        }

    def coverage(self, recommendation):
        """
        This measure the coverage for this recommendation

        :param recommendation: A proposal for recommendation to get the coverage.
        :type recommendation: iterable
        :return: The coverage of the recommendation
        :rtype: float
        """
        if len(recommendation) == 0:
            return 0.
        cached_results = self.mapped_results
        for item in recommendation[:-1]:
            cached_results = cached_results[item]
        if recommendation[-1] in cached_results:
            try:
                return cached_results[recommendation[-1]]["coverage"]
            except KeyError:
                pass
        else:
            cached_results[recommendation[-1]] = {}
        cached_results[recommendation[-1]]["cor"] = genres_out_recommendation = \
            [genre for genre in cached_results.get("cor", list(self.genres.keys()))
             if genre not in self.genre_by_item[recommendation[-1]]]
        for name in genres_out_recommendation:
            p_get_genre = self.genres[name]/self.number_items
            try:
                probability_of_genre = self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))]
            except KeyError:
                self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))] = \
                    binom.pmf(0, len(recommendation), p_get_genre)
                probability_of_genre = self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))]
            try:
                result *= (probability_of_genre ** (1./len(self.genres)))
            except NameError:
                result = probability_of_genre ** (1./len(self.genres))

        try:
            cached_results[recommendation[-1]]["coverage"] = locals().get("result", 0.)
        except KeyError:
            cached_results[recommendation[-1]] = {"coverage": locals().get("result", 0.)}
        return locals().get("result", 0.)

    def non_redundancy(self, recommendation):
        """
        This measure the coverage for this recommendation

        :param recommendation: A proposal for recommendation to get the coverage.
        :type recommendation: iterable
        :return: The coverage of the recommendation
        :rtype: float
        """
        if len(recommendation) == 0:
            return 0.
        cached_results = self.mapped_results
        for item in recommendation[:-1]:
            cached_results = cached_results[item]
        if recommendation[-1] in cached_results:
            try:
                return cached_results[recommendation[-1]]["non redundancy"]
            except KeyError:
                pass
        else:
            cached_results[recommendation[-1]] = {}

        cached_results[recommendation[-1]]["cf"] = genre_frequency = \
            (cached_results.get("cf", Counter()) + Counter(self.genre_by_item[recommendation[-1]]))

        for name, genre_count in genre_frequency.items():
            p_get_genre = self.genres[name]/self.number_items

            try:
                probability_of_genre = self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))]
            except KeyError:
                self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))] = \
                    binom.pmf(0, len(recommendation), p_get_genre)
                probability_of_genre = self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))]
            p_greater_0 = 1. - probability_of_genre

            p_greater_0_and_greater_k = 0
            for i in range(genre_count, int(self.genres[name])+1):
                try:
                    p_equal_i = self.mapped_results["P"]["p(%s=%d)N=%d" % (name, i, len(recommendation))]
                except KeyError:
                    p_equal_i = binom.pmf(i if i < len(recommendation) else len(recommendation), len(recommendation),
                                          p_get_genre)
                    self.mapped_results["P"]["p(%s=%d)N=%d" % (name, i, len(recommendation))] = p_equal_i
                p_greater_0_and_greater_k += p_equal_i
            probability_non_redundancy = (p_greater_0_and_greater_k/p_greater_0) ** (1./len(genre_frequency))
            try:
                result *= probability_non_redundancy
            except NameError:
                result = probability_non_redundancy

        try:
            cached_results[recommendation[-1]]["non redundancy"] = locals().get("result", 0.)
        except KeyError:
            cached_results[recommendation[-1]] = {"non redundancy": locals().get("result", 0.)}
        return locals().get("result", 0.)