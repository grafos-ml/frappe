# -*- coding: utf-8 -*-
"""
Created at September 3 2014

Implementation of the simple diversity for

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from recommendation.diversity.models import Genre, ItemGenre


def weighted_p(p_global, p_local, alpha):
    """
    Measure the frequency for the items for a specific user based on parameter alpha.

    :param p_global: Global probability
    :param p_local: Local probability
    :param alpha: The weight to push toward p_local. The bigger alpha the more influence p_local have
    """
    return (alpha * p_local) + ((1. - alpha) * p_global)


class SimpleDiversity(object):
    """
    A simpler way to imply diversity
    """

    def __init__(self, items, size, user, alpha_constant, lambda_constant):
        number_items = len(items)
        self.recommendation_size = size
        self.lambda_constant = lambda_constant
        self.alpha_constant = alpha_constant
        user_items = user.owned_items
        user_genres = ItemGenre.genre_in((i.item for i in user_items.values()))
        user_items_count = len(user_items)

        self.counter = {}
        for genre in Genre.genre_by_id:
            p_global = Genre.genres_count[genre.pk] / number_items
            p_local = user_genres.get(genre, 0.) / user_items_count if user_items_count else 0.
            self.counter[genre.pk] = int(weighted_p(p_global, p_local, self.alpha_constant) * size)

    def __call__(self, recommendation, item):
        recommendation = recommendation[:]
        genres = ItemGenre.genre_by_item[item]
        dropped = 0
        counter = self.counter
        for genre in genres:
            counter[genre] -= 1
            if counter[genre] < 0:
                dropped += 1
        if dropped < len(genres):
            self.counter = counter
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
        for item in recommendation[:int(2*len(recommendation)/3)]:
            new_recommendation0 = diversity(new_recommendation, item)
            if len(new_recommendation0) != len(new_recommendation) + 1:
                dropped_items.append(item)
            else:
                new_recommendation = new_recommendation0
            if len(new_recommendation) > size:
                break
        return new_recommendation + dropped_items + recommendation[len(new_recommendation)+len(dropped_items):]
