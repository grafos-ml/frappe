#-*- coding: utf-8 -*-
"""
.. py:module:: controller
    :platform: Unix, Windows
    :synopsis: Controller system that provides results. Created on Nov 29, 2013

.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

"""

import numpy as np
from recommender.models import Item
from recommender.caches import CacheUser, CacheMatrix
from recommender.models import TensorModel
from recommender.records.decorators import LogRecommendedApps
import logging


class InterfaceController(object):
    """
    An abstract controller
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor method.

        :param args: Generic anonymous arguments
        :param kwargs: Generic arguments
        """
        self._filters = []
        self._re_rankers = []

    def register_filter(self, *filters):
        """
        Register a filter in this controller queue

        :param filters: A filter to add to the controller
        """
        for f in filters:
            f.controller = self
            self._filters.append(f)

    @property
    def filters(self):
        """
        A list with all the filters registered in this controller
        """
        return self._filters[:]

    def register_reranker(self, *rerankers):
        """
        Register a reranker for this controller.

        :param rerankers: A reranker to add to the controller.
        """
        for r in rerankers:
            r.controller = self
            self._re_rankers.append(r)

    @property
    def rerankers(self):
        """
        A list with all the reranker registered in this controller
        """
        return self._re_rankers[:]

    def get_user_matrix(self):
        """
        Catch the user matrix from database

        :return: The matrix of users.
        """

    def get_apps_matrix(self):
        """
        Catch the app matrix from database

        :return: The matrix of apps.
        """


    @CacheUser()
    def get_app_significance_list(self, user, u_matrix, a_matrix):
        """
        Get a List of significance values for each app

        :param user: The user to get the recommendation
        :param u_matrix: A matrix with one row for each user
        :param a_matrix: A matrix with one row for each app in system

        :return: An array with the app scores for that user
        """
        # Fix user.pk -> user.pk-1: The model was giving recommendation for the
        # previous user.
        return np.squeeze(np.asarray((u_matrix.transpose()[user.pk-1] * a_matrix)))

    @CacheUser()
    @LogRecommendedApps()
    def get_recommendation(self, user, n=10):
        """
        Method to get recommendation according with some user id

        :param user: The user external_id. A way to identify the user.
        :param n: The number of recommendations to give in response.
        :return: A Python list the recommendation apps ids.
        :rtype: list
        """
        result = self.get_app_significance_list(user=user, u_matrix=self.get_user_matrix(),
                                                a_matrix=self.get_apps_matrix())
        logging.debug('Matrix loaded or generated')
        for f in self.filters:
            result = f(user, result, size=n)
        logging.debug('Filters finished')
        result = [aid+1 for aid, _ in sorted(enumerate(result.tolist()), key=lambda x: x[1], reverse=True)]
        for r in self.rerankers:
            result = r(user, result, size=n)
        logging.debug('Re-rankers finished')
        return result[:n]

    def get_recommendations_items(self, user, n=10):
        """
        Returns the recommendations with a list of external_is's

        :param user: See parent
        :param n: See parent
        :return: Item external id list
        """
        result = self.get_recommendation(user=user, n=n)
        rs = {app.pk: app for app in Item.objects.filter(pk__in=result)}
        return [rs[r] for r in result]

    def get_external_id_recommendations(self, user, n=10):
        """
        Returns the recommendations with a list of external_is's

        :param user: Same parameters that get_app_significance
        :param n:
        :return: Item external id list
        """
        result = self.get_recommendation(user=user, n=n)
        rs = {app_id: app_eid for app_id, app_eid in Item.objects.filter(pk__in=result).values_list('pk',
                                                                                                    'external_id')}
        return [rs[r] for r in result]


class Recommender(InterfaceController):
    """
    Get the matrix from the Model
    """

    def get_user_matrix(self):
        """
        Catch the user matrix from database

        :return: The matrix of users.
        """
        try:
            return TensorModel.objects.filter(dim=0).order_by('-id')[0].numpy_matrix
        except IndexError:
            TensorModel.train()
            return self.get_user_matrix()

    @CacheMatrix()
    def get_apps_matrix(self):
        """
        Cathe matrix from model

        :return: The matrix of apps.
        """
        try:
            return TensorModel.objects.filter(dim=1).order_by('-id')[0].numpy_matrix
        except IndexError:
            TensorModel.train()
            return  self.get_apps_matrix()