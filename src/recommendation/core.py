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
from recommendation.records.decorators import LogRecommendedApps
from recommendation.model_factory import TensorCoFi, Popularity
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

    @staticmethod
    def get_model():
        """
        Catch model

        :return: The Model
        """
        raise NotImplemented

    @staticmethod
    def get_alternative(user):
        """
        Return the popular items
        :return: list
        """
        raise NotImplemented

    def online_user_factors(self, Y, user_item_ids, p_param=10, lambda_param=0.01):
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
    def get_recommendation_from_model(self, user):
        """
        Get a List of significance values for each app

        :param user: The user to get the recommendation
        :param u_matrix: A matrix with one row for each user
        :param a_matrix: A matrix with one row for each app in system

        :return: An array with the app scores for that user
        """
        # Fix user.pk -> user.pk-1: The model was giving recommendation for the
        # previous user.
        model = self.get_model()
        if user.pk-1 >= model.factors[0].shape[0]:  # We have a new user, so lets construct factors for him:
            apps_idx = [a.pk - 1 for a in user.owned_items if a.pk - 1 <= model.factors[1].shape[0]]
            if len(apps_idx) < 3:
                raise ValueError
            u_factors = model.online_user_factors(apps_idx)
            return np.squeeze(np.asarray((u_factors * model.factors[1].transpose())))
        else:
            return model.get_recommendation(user)

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
            result = self.get_recommendation_from_model(user=user)
        except Exception:
            print("Wild error appear in core recommendation")
            result = self.get_alternative(user)
        logging.debug("Matrix loaded or generated")
        for f in self.filters:
            result = f(user, result, size=n)
        logging.debug("Filters finished")
        result = [aid+1 for aid, _ in sorted(enumerate(result), key=lambda x: x[1], reverse=True)]
        for r in self.rerankers:
            result = r(user, result, size=n)
        logging.debug("Re-rankers finished")
        return result[:n]
        #return self.run_re_rankers(recommendation=list(enumerate(result, start=1)), n=n)

    def get_external_id_recommendations(self, user, n=10):
        """
        Returns the recommendations with a list of external_is's

        :param user: Same parameters that get_app_significance
        :param n:
        :return: Item external id list
        """
        result = self.get_recommendation(user=user, n=n)
        rs = Item.all_items()
        #return [rs[r] for r in result]
        return [rs[r]["external_id"] for r in result]

    def run_re_rankers(self, recommendation, n):
        """

        """
        result, dropped = [], []
        while len(result) < n:
            item = max(recommendation, key=lambda x: x[1])
            recommendation.remove(item)
            if all(map(lambda x: x(item, result, dropped), self.rerankers)):
                result.append(item[0])
            else:
                dropped.append(item)
        return result


class TensorCoFiRecommender(InterfaceController):
    """
    Get the matrix from the Model
    """

    @staticmethod
    def get_model():
        """
        Catch model

        :return: The Model
        """
        return TensorCoFi.get_model()

    @staticmethod
    def get_alternative(user):
        """
        Return the popular items
        :return: list
        """
        return Popularity.get_model().recommendation

DEFAULT_SETTINGS = {
    "default": {
        "core": ("recommendation.core", "TensorCoFiRecommender"),
        "filters": [
            ("recommendation.filter_owned.filters", "FilterOwnedFilter"),
            ("recommendation.language.filters", "SimpleLocaleFilter"),
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
    args, kwargs = engine_settings.get("core params", ((), {}))
    RECOMMENDATION_ENGINES[engine] = getattr(__import__(rec_mod, fromlist=[""]), rec_class)(*args, **kwargs)

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