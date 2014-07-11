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
from django.core.cache import get_cache
from recommendation.diversity.models import Genre
from recommendation.diversity.rerankers.utils import weighted_p, normalize


class BinomialDiversity(object):
    """
    Binomial diversity implementation of the paper that is described in the module
    """

    genre_by_item = None
    genres = None
    recommendation_size = None
    number_items = None

    def __init__(self, user, items, size, alpha_constant, lambda_constant):
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
        self.genre_by_item = {item: [] for item in items}
        self.genres = {}
        for item_id, genre in genres:
            self.genres[genre] = self.genres.get(genre, 1.) + 1.
            self.genre_by_item[item_id].append(genre)
        self.number_items = len(items)
        self.recommendation_size = size
        self.lambda_constant = lambda_constant
        self.alpha_constant = alpha_constant
        user_genres = {}
        self.user_items_count = 0
        for iid, genre in Genre.objects.filter(items__in=user.owned_items).values_list("items__id", "name"):
            user_genres[genre] = user_genres.get(genre, 1.) + 1.
            self.user_items_count += 1
        self.p_genre_cache = {}
        for genre, genre_count in self.genres.items():
            p_global = genre_count / self.number_items
            p_local = user_genres.get(genre, 0.) / self.user_items_count if self.user_items_count else 0.
            self.p_genre_cache[genre] = weighted_p(p_global, p_local, self.alpha_constant)

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

        result = 1.
        for name in genres_out_recommendation:
            p_get_genre = self.p_genre_cache[name]
            probability_of_genre = binom.pmf(0, len(recommendation), p_get_genre) ** (1./len(self.genres))
            result *= probability_of_genre
        return result

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
        result = 1.
        for name, genre_count in genres_frequency:
            p_get_genre = self.p_genre_cache[name]
            p_greater_0 = 1 - binom.pmf(0, len(recommendation), p_get_genre)
            gc = genre_count-1 if genre_count else 0
            p_greater_0_and_greater_k = 1. - binom.cdf(gc, len(recommendation), p_get_genre)
            probability_non_redundancy = (p_greater_0_and_greater_k/p_greater_0) ** (1./len(genres_frequency))

            result *= probability_non_redundancy
        return result

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
        div0, div1 = self.diversity(recommendation), self.diversity(recommendation+[item_id])
        div = div1 - div0

        # Assume that the mean is 0 (it have the same probability of improving and of getting worse). The variance of
        # 0.25 is a guess that the improvement never goes beyond imagination(:s)
        normalized_div = normalize(div, 0., 0.25)
        return (1.-self.lambda_constant)*normalized_rank + self.lambda_constant*normalized_div


class BinomialDiversityReRanker(object):
    """
    The greedy re-ranker that build a new recommendation by choosing the max diversity item in the head of the old
     recommendation. It iterates this process until have a new recommendation.
    """

    def __init__(self, alpha_constant=0.9, lambda_constant=1.):  # Set lambda lower to improve user tendencies
        """
        Constructor

        :param lambda_constant: Some weight. It has to be between 0 and 1. Default is 0.5.
        :type lambda_constant: float
        :return:
        """
        self.lambda_constant = lambda_constant
        self.alpha_constant = alpha_constant

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
        size_boost = 100
        recommendation_set = recommendation[:size_boost]
        diversity = NeoBinomialDiversity(user, recommendation_set, size, self.alpha_constant, self.lambda_constant)
        new_recommendation = []
        for _ in range(size):
            div_list = ((item, diversity(new_recommendation, (index, item)))
                        for index, item in enumerate(recommendation_set, start=1))
            chosen_item = max(div_list, key=lambda x: x[1])[0]
            recommendation_set.remove(chosen_item)
            new_recommendation.append(chosen_item)
            diversity.update()
        result = new_recommendation + recommendation_set + recommendation[size_boost:]
        #assert len(result) == len(recommendation), "The result lost or gained elements"
        return result


class TurboBinomialDiversity(BinomialDiversity):
    """
    Implementation of BinomialDiversity with improvement by reducing the redundancy calculations. This will be done by
    mapping the tree of results and using this trees in the calculations.
    """

    mapped_results = None

    def __init__(self, user, items, size, alpha_constant, lambda_constant):
        """
        Constructor

        :param items: A list with the items ids
        :type items: list
        :param size: The size of the recommendation
        :type size: int
        :param lambda_constant: Lambda constant. Must be between 0 and 1.
        :type lambda_constant: float
        """
        super(TurboBinomialDiversity, self).__init__(user, items, size, alpha_constant, lambda_constant)
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
            cor = list(self.genres.keys())
            cov = 1.
            try:
                self.mapped_results["[]"]["cor"] = cor
                self.mapped_results["[]"]["coverage"] = 1.
            except KeyError:
                self.mapped_results["[]"] = {
                    "cor": cor, "coverage": cov
                }
            return 1.

        # Search in cached results
        cache_key = str(recommendation)
        cached_results = self.mapped_results.get(cache_key, {})
        try:
            return cached_results["coverage"]
        except KeyError:
            pass

        # Calculate new coverage value
        result = 1.
        try:
            genres_out_recommendation = cached_results["cor"]
        except KeyError:
            genres_out_recommendation = \
                self.mapped_results[str(recommendation[:-1])]["cor"][:]
            for g in self.genre_by_item[recommendation[-1]]:
                try:
                    genres_out_recommendation.remove(g)
                except ValueError:
                    pass
            cached_results["cor"] = genres_out_recommendation
        for name in genres_out_recommendation:
            p_get_genre = self.p_genre_cache[name]
            try:
                probability_of_genre = self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))]
            except KeyError:
                self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))] = \
                    binom.pmf(0, len(recommendation), p_get_genre)
                probability_of_genre = self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))]

            result *= (probability_of_genre ** (1./len(self.genres)))

        cached_results["coverage"] = result
        self.mapped_results[cache_key] = cached_results
        return result

    def non_redundancy(self, recommendation):
        """
        This measure the coverage for this recommendation

        :param recommendation: A proposal for recommendation to get the coverage.
        :type recommendation: iterable
        :return: The coverage of the recommendation
        :rtype: float
        """
        if len(recommendation) == 0:
            nr = 1,
            cf = Counter()
            try:
                self.mapped_results["[]"]["non redundancy"] = nr
                self.mapped_results["[]"]["cf"] = cf
            except KeyError:
                self.mapped_results["[]"] = {
                    "non redundancy": nr, "cf": cf
                }
            return 1.

        # Search in cached results
        cache_key = str(recommendation)
        cached_results = self.mapped_results.get(cache_key, {})
        try:
            return cached_results["non redundancy"]
        except KeyError:
            pass

        # Calculate new non-redundancy value
        cached_results["cf"] = genre_frequency = \
            (self.mapped_results[str(recommendation[:-1])]["cf"] + Counter(self.genre_by_item[recommendation[-1]]))

        result = 1.
        for name, genre_count in genre_frequency.items():
            p_get_genre = self.p_genre_cache[name]
            if p_get_genre != 0:
                try:
                    probability_of_genre = self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))]
                except KeyError:
                    self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))] = \
                        binom.pmf(0, len(recommendation), p_get_genre)
                    probability_of_genre = self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))]
                p_greater_0 = 1. - probability_of_genre

                try:
                    p_greater_0_and_greater_k = self.mapped_results["P"]["p(%s>=%d)N=%d" % (name, genre_count,
                                                                                            len(recommendation))]
                except KeyError:
                    gc = genre_count-1 if genre_count else 0
                    p_greater_0_and_greater_k = 1. - binom.cdf(gc, len(recommendation), p_get_genre)
                    self.mapped_results["P"]["p(%s>=%d)N=%d" % (name, genre_count, len(recommendation))] = \
                        p_greater_0_and_greater_k

                probability_non_redundancy = (p_greater_0_and_greater_k/p_greater_0)
            else:
                probability_non_redundancy = 0.

            result *= (probability_non_redundancy ** (1./len(genre_frequency)))

        cached_results["non redundancy"] = result
        self.mapped_results[cache_key] = cached_results
        return cached_results["non redundancy"]


class NeoBinomialDiversity(BinomialDiversity):
    """
    Binomial diversity implementation of the paper that is described in the module
    """

    mapped_results = None

    def __init__(self, user, items, size, alpha_constant, lambda_constant):
        """
        Constructor

        :param items: A list with the items ids
        :type items: list
        :param size: The size of the recommendation
        :type size: int
        :param lambda_constant: Lambda constant. Must be between 0 and 1.
        :type lambda_constant: float
        """
        super(NeoBinomialDiversity, self).__init__(user, items, size, alpha_constant, lambda_constant)
        self.mapped_results = get_cache("default").get("diversity_p", {"P": {}})

    def update(self):
        get_cache("default").set("diversity_p", self.mapped_results)

    def coverage(self, recommendation):
        """
        This measure the coverage for this recommendation

        :param recommendation: A proposal for recommendation to get the coverage.
        :type recommendation: iterable
        :return: The coverage of the recommendation
        :rtype: float
        """
        if len(recommendation) == 0:
            cor = list(self.genres.keys())
            cov = 1.
            try:
                self.mapped_results["[]"]["cor"] = cor
                self.mapped_results["[]"]["coverage"] = 1.
            except KeyError:
                self.mapped_results["[]"] = {
                    "cor": cor, "coverage": cov
                }
            return 1.

        # Search in cached results
        cache_key = str(recommendation)
        cached_results = self.mapped_results.get(cache_key, {})
        try:
            return cached_results["coverage"]
        except KeyError:
            pass

        # Calculate new coverage value
        result = 1.
        try:
            genres_out_recommendation = cached_results["cor"]
        except KeyError:
            genres_out_recommendation = \
                self.mapped_results[str(recommendation[:-1])]["cor"][:]
            for g in self.genre_by_item[recommendation[-1]]:
                try:
                    genres_out_recommendation.remove(g)
                except ValueError:
                    pass
            cached_results["cor"] = genres_out_recommendation
        for name in genres_out_recommendation:
            p_get_genre = self.p_genre_cache[name]
            try:
                probability_of_genre = self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))]
            except KeyError:
                self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))] = \
                    binom.pmf(0, len(recommendation), p_get_genre)
                probability_of_genre = self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))]

            result *= (probability_of_genre ** (1./len(self.genres)))

        cached_results["coverage"] = result
        self.mapped_results[cache_key] = cached_results
        return result

    def non_redundancy(self, recommendation):
        """
        This measure the coverage for this recommendation

        :param recommendation: A proposal for recommendation to get the coverage.
        :type recommendation: iterable
        :return: The coverage of the recommendation
        :rtype: float
        """
        if len(recommendation) == 0:
            nr = 1,
            cf = Counter()
            try:
                self.mapped_results["[]"]["non redundancy"] = nr
                self.mapped_results["[]"]["cf"] = cf
            except KeyError:
                self.mapped_results["[]"] = {
                    "non redundancy": nr, "cf": cf
                }
            return 1.

        # Search in cached results
        cache_key = str(recommendation)
        cached_results = self.mapped_results.get(cache_key, {})
        try:
            return cached_results["non redundancy"]
        except KeyError:
            pass

        # Calculate new non-redundancy value
        cached_results["cf"] = genre_frequency = \
            (self.mapped_results[str(recommendation[:-1])]["cf"] + Counter(self.genre_by_item[recommendation[-1]]))

        result = 1.
        for name, genre_count in genre_frequency.items():
            p_get_genre = self.p_genre_cache[name]
            if p_get_genre != 0:
                try:
                    probability_of_genre = self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))]
                except KeyError:
                    self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))] = \
                        binom.pmf(0, len(recommendation), p_get_genre)
                    probability_of_genre = self.mapped_results["P"]["p(%s=0)N=%d" % (name, len(recommendation))]
                p_greater_0 = 1. - probability_of_genre

                try:
                    p_greater_0_and_greater_k = self.mapped_results["P"]["p(%s>=%d)N=%d" % (name, genre_count,
                                                                                            len(recommendation))]
                except KeyError:
                    gc = genre_count-1 if genre_count else 0
                    p_greater_0_and_greater_k = 1. - binom.cdf(gc, len(recommendation), p_get_genre)
                    self.mapped_results["P"]["p(%s>=%d)N=%d" % (name, genre_count, len(recommendation))] = \
                        p_greater_0_and_greater_k

                probability_non_redundancy = (p_greater_0_and_greater_k/p_greater_0)
            else:
                probability_non_redundancy = 0.

            result *= (probability_non_redundancy ** (1./len(genre_frequency)))

        cached_results["non redundancy"] = result
        self.mapped_results[cache_key] = cached_results
        return cached_results["non redundancy"]