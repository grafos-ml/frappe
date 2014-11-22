# -*- coding: utf-8 -*-
"""
Created at September 3 2014

Implementation of the simple diversity for

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

import numpy as np
from frappe.tools.diversity.models import Genre, ItemGenre
from blist import blist


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

        user_items = user.owned_items
        user_genres = ItemGenre.genre_in((item for item in user_items.values()))
        user_items_count = len(user_items)

        self.counter = {}
        for genre_id in Genre.get_all_genres():
            genre = Genre.get_genre_by_id(genre_id)
            try:
                p_global = genre.count_items / number_items
            except ZeroDivisionError:
                p_global = 0.
            try:
                p_local = user_genres.get(genre, 0.) / user_items_count
            except ZeroDivisionError:
                p_local = 0.
            self.counter[genre.pk] = int(weighted_p(p_global, p_local, alpha_constant) * size)

    def __call__(self, recommendation, item_eid):
        genres = ItemGenre.get_genre_by_item(item_eid)
        dropped = 0
        for genre in genres:
            self.counter[genre] -= 1
            if self.counter[genre] < 0:
                dropped += 1
        # Change "<" to "<=" improve greatly
        if dropped <= len(genres):
            #recommendation.append(item)
            return True
        return False
        #return recommendation


class SimpleDiversityReRanker(object):
    """
    The greedy re-ranker that build a new recommendation by choosing the max diversity item in the head of the old
     recommendation. It iterates this process until have a new recommendation.
    """

    def __init__(self, alpha_constant=.8, lambda_constant=1.):  # Set lambda lower to improve user tendencies
        """
        Constructor

        :param lambda_constant: Some weight. It has to be between 0 and 1. Default is 0.5.
        :type lambda_constant: float
        :return:
        """
        self.lambda_constant = lambda_constant
        self.alpha_constant = alpha_constant

    def __call__(self, module, user, recommendation, size, *args, **kwargs):
        """

        :param module: The recommendation module
        :type module: Module
        :param user: The user that want the recommendation
        :type user: User
        :param recommendation: The recommendation to re-rank
        :type recommendation: numpy.array
        :param size: The size of the recommendation asked
        :type size: int
        :return: The re-ranked recommendation
        :rtype: list
        """
        diversity = SimpleDiversity(recommendation, size, user, self.alpha_constant, self.lambda_constant)
        new_recommendation = np.empty((size,), dtype=recommendation.dtype)
        dropped_items = blist()
        index = 0
        iterator = iter(recommendation)
        while index < size:
            try:
                item = iterator.next()
            except StopIteration:
                break
            if diversity(new_recommendation, item):
                new_recommendation[index] = item
                index += 1
            else:
                dropped_items.append(item)
        #for item_id in recommendation:
        #    if diversity(new_recommendation, item_id):
        #        new_recommendation.append(item_id)
        #    else:
        #        dropped_items.append(item_id)
        #    if len(new_recommendation) > size:
        #        break
        return np.concatenate((new_recommendation, dropped_items,
                               recommendation[index+len(dropped_items):])).astype(recommendation.dtype)
