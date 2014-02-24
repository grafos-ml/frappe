#-*- coding: utf-8 -*-
"""
.. py:module:: controller
    :platform: Unix, Windows
    :synopsis: Controller system that provides results. Created on Nov 29, 2013

.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

"""

import numpy as np
from ffos.models import FFOSApp
from ffos.recommender.caches import CacheUser, CacheMatrix
from ffos.recommender.models import TensorModel
from ffos.recommender.rlogging.decorators import LogRecommendedApps
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
        self._rerankers = []

    def registerFilter(self, *filters):
        """
        Register a filter in this controller queue

        **Args**

        filter *Filter*:
            A filter to add to the controller
        """
        for filter in filters:
            filter.controller = self
            self._filters.append(filter)

    @property
    def filters(self):
        """
        A list with all the filters registered in this controller
        """
        return self._filters[:]

    def registerReranker(self, *rerankers):
        """
        Register a reranker for this controller.

        **Args**

        reranker *Reranker*:
            A reranker to add to the controller.
        """
        for reranker in rerankers:
            reranker.controller = self
            self._rerankers.append(reranker)

    @property
    def rerankers(self):
        """
        A list with all the reranker registered in this controller
        """
        return self._rerankers[:]

    def get_user_matrix(self):
        """
        Catch the user matrix from database

        **Returns**

        *np.matrix*:
            The matrix of users.
        """

    def get_apps_matrix(self):
        """
        Catch the app matrix from database

        **Returns**

        *np.matrix*:
            The matrix of apps.
        """


    @CacheUser()
    def get_app_significance_list(self, user, u_matrix, a_matrix):
        """
        Get a List of significance values for each app

        **Args**

        user *basestring or FFOSUser*:
            The user to get the recommendation

        u_matrix *np.matrix*:
            A matrix with one row for each user

        a_matrix *np.matrix*:
            A matrix with one row for each app in system

        **Return**

        *np.array*:
            An array with the app scores for that user
        """
        # Fix user.pk -> user.pk-1: The model was giving recommendation for the
        # previous user.
        return np.squeeze(np.asarray((u_matrix.transpose()[user.pk-1] * a_matrix)))

    @CacheUser()
    @LogRecommendedApps()
    def get_recommendation(self, user, n=10):
        """
        Method to get recommendation according with some user id

        **Args**

        user *FFOSUser*:
            The user external_id. A way to identify the user.

        n *int*:
            The number of recommendations to give in response.

        **Returns**

        *list*:
            A Python list the recommendation apps ids.
        """
        print ""
        result = self.get_app_significance_list(user=user, u_matrix=self.get_user_matrix(),
                                                a_matrix=self.get_apps_matrix())
        logging.debug('Matrix loaded or generated')
        for _filter in self.filters:
            result = _filter(user, result, size=10)
        logging.debug('Filters finished')
        result = [aid+1 for aid, _ in sorted(enumerate(result.tolist()), cmp=lambda x, y: cmp(y[1], x[1]))]
        for _reranker in self.rerankers:
            result = _reranker(user, result, size=10)
        logging.debug('Re-rankers finished')
        return result[:n]

    def get_recommendations_items(self, user, n=10):
        """
        Returns the recommendations with a list of external_is's

        **Args**

            Same parameters that get_app_significance

        **Returns**

            *list*:
                FFOSApp external id list
        """
        result = self.get_recommendation(user=user, n=n)
        rs = {app.pk: app for app in FFOSApp.objects.filter(pk__in=result)}
        return [rs[r] for r in result]

    def get_external_id_recommendations(self, user, n=10):
        """
        Returns the recommendations with a list of external_is's

        **Args**

            Same parameters that get_app_significance

        **Returns**

            *list*:
                FFOSApp external id list
        """
        result = self.get_recommendation(user=user, n=n)
        rs = {app_id: app_eid for app_id, app_eid in FFOSApp.objects.filter(pk__in=result).values_list('pk',
                                                                                                       'external_id')}
        return [rs[r] for r in result]


class SimpleController(InterfaceController):
    """
    Get the matrix from the Model
    """

    def get_user_matrix(self):
        """
        Catch the user matrix from database

        **Returns**

        *np.matrix*:
            The matrix of users.
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

        **Returns**

        *np.matrix*:
            The matrix of apps.
        """
        try:
            return TensorModel.objects.filter(dim=1).order_by('-id')[0].numpy_matrix
        except IndexError:
            TensorModel.train()
            return  self.get_apps_matrix()