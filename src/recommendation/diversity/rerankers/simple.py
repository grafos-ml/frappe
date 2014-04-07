# -*- coding: utf-8 -*-
"""
Created at 25 February 2014

Implementation of the simple diversity for

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from recommendation.diversity.models import Genre
from recommendation.diversity.rerankers.utils import weighted_p


class SimpleDiversity(object):
    """
    A simpler way to imply diversity
    """

    def __init__(self, items, size, user, alpha_constant, lambda_constant):
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
        for iid, genre in Genre.objects.filter(items__in=user.owned_items.all()).values_list("items__id", "name"):
            user_genres[genre] = user_genres.get(genre, 1.) + 1.
            self.user_items_count += 1
        self.counter = {}
        for _, genre in genres:
            p_global = self.genres[genre] / self.number_items
            p_local = user_genres.get(genre, 0.) / self.user_items_count if self.user_items_count else 0.
            self.counter[genre] = weighted_p(p_global, p_local, self.alpha_constant) * size
            self.counter[genre] = int(self.counter[genre])
        print(self.counter)

    def __call__(self, recommendation, item):
        recommendation = recommendation[:]
        genres = self.genre_by_item[item]
        dropped = 0
        for genre in genres:
            self.counter[genre] -= 1
            if self.counter[genre] < 0:
                dropped += 1
        if dropped < len(genres):
            recommendation.append(item)
        return recommendation


class SimpleDiversityReRanker(object):
    """
    The greedy re-ranker that build a new recommendation by choosing the max diversity item in the head of the old
     recommendation. It iterates this process until have a new recommendation.
    """

    def __init__(self, alpha_constant=0.8, lambda_constant=1.):  # Set lambda lower to improve user tendencies
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
        diversity = SimpleDiversity(recommendation, size, user, self.alpha_constant, self.lambda_constant)
        new_recommendation = []
        dropped_items = []
        for item in recommendation:
            new_recommendation0 = diversity(new_recommendation, item)
            if len(new_recommendation0) != len(new_recommendation) + 1:
                dropped_items.append(item)
            else:
                new_recommendation = new_recommendation0
            if len(new_recommendation) > size:
                break
        return new_recommendation + dropped_items + recommendation[size+len(dropped_items):]
