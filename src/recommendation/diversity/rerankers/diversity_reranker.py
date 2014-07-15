#! -*- encoding: utf-8 -*-
"""
Cached binomial diversity
"""
__author__ = 'joaonrb'

from scipy.stats import binom
from django.core.cache import get_cache
from recommendation.models import Item
from recommendation.diversity.models import Genre
from recommendation.diversity.rerankers.utils import weighted_p, normalize
from recommendation.diversity.rerankers.binomial import TurboBinomialDiversity


class IDiversity(object):
    """
    Interface for diversity algorithms for using in Diversity re-ranker
    """

    def __call__(self, recommendation, item):
        raise NotImplemented


class Binomial(IDiversity):
    """
    Binomial diversity implementation of the paper that is described in the module:

    for genre not in recommendation:
        yield
    """

    def __init__(self, user, alpha_constant, lambda_constant):
        self.cache = get_cache("default")
        self.lambda_constant = lambda_constant
        self.alpha_constant = alpha_constant
        self.user_items = user.items.count()

    def binomial_pmf(self, k, n, p):
        """
        Binomial density for k success in n trials with p probability of success
        :param k: Number of success
        :param n: Number of trials
        :param p: Probability of success
        :return: The probability
        """
        key = "PxEk_xISbinom_nIS%d_pIS%f_AND_kIS%d" % (k, n, p)
        result = self.cache.get(key)
        if not result:
            result = binom.pmf(k, n, p)
            self.cache.set(key, result, None)
        return result

    def binomial_cdf(self, k, n, p):
        """
        Binomial density for k success in n trials with p probability of success
        :param k: Number of success
        :param n: Number of trials
        :param p: Probability of success
        :return: The probability
        """
        key = "PxMEk_xISbinom_nIS%d_pIS%f_AND_kIS%d" % (k, n, p)
        result = self.cache.get(key)
        if not result:
            result = binom.cdf(k, n, p)
            self.cache.set(key, result, None)
        return result

    def coverage(self, recommendation_size, genre_size, p_item_has_genre):
        """
        Calculate the coverage base on the size of recommendation, the number of genres and the probability of that
        genres is in recommendation.
        :param recommendation_size: The size of this recommendation
        :param genre_size: The number of genres that exist in items(over the all items)
        :param p_item_has_genre: List of probabilities for genre to appear in a random item.
        :return: The amount of coverage such a recommendation achieve.
        """
        key = "cv_%d_%d_%s" % (recommendation_size, genre_size, p_item_has_genre)
        coverage = self.cache.get(key)
        if not coverage:
        #if True:
            coverage = 1.
            for p_genre in p_item_has_genre:
                probability_of_genre = self.binomial_pmf(0, recommendation_size, p_genre) ** (1./genre_size)
                coverage *= probability_of_genre
            self.cache.set(key, coverage)
        return coverage

    def non_redundancy(self, recommendation_size, genre_p_and_freq_in_rec):
        key = "nr_%d_%s" % (recommendation_size, genre_p_and_freq_in_rec)
        non_redundancy = self.cache.get(key)
        if not non_redundancy:
        #if True:
            non_redundancy = 1.
            for p_genre, frequency_genre in genre_p_and_freq_in_rec:
                p_greater_0 = 1 - self.binomial_pmf(0, recommendation_size, p_genre)
                p_greater_0_and_greater_k = 1. - self.binomial_cdf(frequency_genre-1 if frequency_genre else 0,
                                                                   recommendation_size, p_genre)
                probability_non_redundancy = \
                    (p_greater_0_and_greater_k/p_greater_0) ** (1./len(genre_p_and_freq_in_rec))
                non_redundancy *= probability_non_redundancy
            self.cache.set(key, non_redundancy)
        return non_redundancy

    def get_diversity(self, recommendation):
        """
        Check the diversity of this propose of recommendation.

        :param recommendation: Recommendation to evaluate.
        :type recommendation: list
        :return: The diversity measure. The higher the better(high diversity with low redundancy)
        :rtype: float
        """
        rec_size = len(recommendation)
        genre_size = Genre.count_all()
        items_size = len(Item.all_items())
        genres = Genre.genre_in(recommendation)  # frequency in rec, frequency in DB
        get_p = lambda x: weighted_p(x[1]/items_size, x[0]/self.user_items, self.alpha_constant)
        p_item_has_genre = map(get_p, genres)
        genre_gp_and_lfreq = map(lambda x: (get_p(x), x[0]), genres)
        return self.coverage(rec_size, genre_size, p_item_has_genre) * self.non_redundancy(rec_size, genre_gp_and_lfreq)

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
        normalized_rank = normalize(rank, 0.5*(1+len(Item.all_items())), (1./12)*(len(Item.all_items())-1)**2)
        div0, div1 = self.get_diversity(recommendation), self.get_diversity(recommendation+[item_id])
        div = div1 - div0

        # Assume that the mean is 0 (it have the same probability of improving and of getting worse). The variance of
        # 0.25 is a guess that the improvement never goes beyond imagination(:s)
        normalized_div = normalize(div, 0., 0.25)
        return (1.-self.lambda_constant)*normalized_rank + self.lambda_constant*normalized_div


class DiversityReRanker(object):
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
        depth = size if "depth" in kwargs else kwargs["depht"]
        r_set = recommendation
        #diversity = TurboBinomialDiversity(user, recommendation_set, size, self.alpha_constant, self.lambda_constant)
        diversity = Binomial(user, self.alpha_constant, self.lambda_constant)
        new_recommendation = []
        while len(new_recommendation) != size:
            div_list = ((r_set[i], diversity(new_recommendation, (i+1, r_set[1]))) for i in range(depth))
            chosen_item, _ = max(div_list, key=lambda x: x[1])
            r_set.remove(chosen_item)
            new_recommendation.append(chosen_item)
            #diversity.update()
        result = new_recommendation + r_set + recommendation
        #assert len(result) == len(recommendation), "The result lost or gained elements"
        return result