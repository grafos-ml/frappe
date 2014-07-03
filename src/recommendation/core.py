#-*- coding: utf-8 -*-
"""
.. py:module:: controller
    :platform: Unix, Windows
    :synopsis: Controller system that provides results. Created on Nov 29, 2013

.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

"""

import numpy as np
from django.conf import settings
from recommendation.models import Item
from recommendation.caches import CacheUser
from recommendation.models import TensorModel, PopularityModel
from recommendation.records.decorators import LogRecommendedApps
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

    def online_user_factors(self, Y, user_item_ids, p_param = 10, lambda_param = 0.01):
        """
        :param Y: application matrix Y.shape = (#apps, #factors)
        :param user_item_ids: the rows that correspond to installed applications in Y matrix
        :param p_param: p parameter
        :param lambda_param: regulerizer

        >>> pyTF = PyTensorCoFi()
        >>> Y = np.array([[-1.0920831, -0.01566422], [-0.8727925, 0.22307773], [0.8753245, -0.80181429], \
                          [-0.1338534, -0.51448172], [-0.2144651, -0.96081265]])
        >>> user_items = [1,3,4]
        >>> pyTF.online_user_factors(Y, user_items, p_param=10, lambda_param=0.01)
        array([-1.18324547, -0.95040477])
        """
        y = Y[user_item_ids]
        base1 = Y.transpose().dot(Y)
        base2 = y.transpose().dot(np.diag([p_param - 1] * y.shape[0])).dot(y)
        base = base1 + base2 + np.diag([lambda_param] * base1.shape[0])
        u_factors = np.linalg.inv(base).dot(y.transpose()).dot(np.diag([p_param] *
                                                                       y.shape[0])).dot(np.ones(y.shape[0]).transpose())
        return u_factors

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

        if user.pk-1 > u_matrix.shape[0]:  # We have a new user, so lets construct factors for him:
            apps_idx = [a.pk - 1 for a in user.items.all() if a.pk - 1 < a_matrix.shape[1]]
            if len(apps_idx) < 3:
                raise ValueError
            u_factors = self.online_user_factors(a_matrix.transpose(), apps_idx)
            return np.squeeze(np.asarray((u_factors * a_matrix)))
        else:
            return np.squeeze(np.asarray((u_matrix.transpose()[user.pk-1] * a_matrix)))

    def get_popularity(self):
        """
        Return the popular items
        :return: list
        """
        return PopularityModel.get_popularity().recommendation

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
        try:
            result = self.get_app_significance_list(user=user, u_matrix=self.get_user_matrix(),
                                                    a_matrix=self.get_apps_matrix())
        except ValueError:
            print("POPULARITY")
            result = self.get_popularity()
        logging.debug("Matrix loaded or generated")
        for f in self.filters:
            result = f(user, result, size=n)
        logging.debug("Filters finished")
        result = [aid+1 for aid, _ in sorted(enumerate(result.tolist()), key=lambda x: x[1], reverse=True)]
        for r in self.rerankers:
            result = r(user, result, size=n)
        logging.debug("Re-rankers finished")
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
        rs = Item.all_items()
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
        return TensorModel.get_user_matrix().numpy_matrix

    def get_apps_matrix(self):
        """
        Cathe matrix from model

        :return: The matrix of apps.
        """
        return TensorModel.get_item_matrix().numpy_matrix

DEFAULT_SETTINGS = {
    "default": {
        "core": ("recommendation.core", "Recommender"),
        "filters": [

        ],
        "rerankers": [
            ("recommendation.records.rerankers", "SimpleLogReRanker"),
            ("recommendation.diversity.rerankers", "DiversityReRanker")
        ]
    }
}

try:
    RECOMMENDATION_SETTINGS = getattr(settings, "RECOMMENDATION_SETTINGS")
except AttributeError:
    RECOMMENDATION_SETTINGS = DEFAULT_SETTINGS

RECOMMENDATION_ENGINES = {}
for engine, engine_settings in RECOMMENDATION_SETTINGS.items():
    rec_mod, rec_class = engine_settings["core"]

    RECOMMENDATION_ENGINES[engine] = getattr(__import__(rec_mod, fromlist=[""]), rec_class)()

    # Register Filters
    for mod, filter_class in engine_settings["filters"]:
        RECOMMENDATION_ENGINES[engine].register_filter(getattr(__import__(mod, fromlist=[""]), filter_class)())

    # Register re-rankers
    for mod, reranker_class in RECOMMENDATION_SETTINGS["default"]["rerankers"]:
        RECOMMENDATION_ENGINES[engine].register_reranker(getattr(__import__(mod, fromlist=[""]), reranker_class)())

# Set default Recommendation engine
DEFAULT_RECOMMENDATION = RECOMMENDATION_ENGINES["default"]

if __name__ == "__main__":
    import doctest
    doctest.testmod()