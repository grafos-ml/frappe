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
import sys
if sys.version_info >= (3, 0):
    basestring = unicode = str


class IController(object):
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

    def get_model(self, user):
        """
        Catch model

        :return: The Model
        """
        raise NotImplemented

    def get_alternative(self, user):
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
        model = self.get_model(user)
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


class TensorCoFiRecommender(IController):
    """
    Get the matrix from the Model
    """

    def get_model(self, user):
        """
        Catch model

        :return: The Model
        """
        return TensorCoFi.get_model()

    def get_alternative(self, user):
        """
        Return the popular items
        :return: list
        """
        return Popularity.get_model().recommendation

DEFAULT_SETTINGS = {
    "default": {
        "core": "recommendation.core.TensorCoFiRecommender",
        "filters": [
            "recommendation.filter_owned.filters.FilterOwnedFilter",
            "recommendation.language.filters.SimpleLocaleFilter",
        ],
        "rerankers": [
            "recommendation.records.rerankers.SimpleLogReRanker",
            "recommendation.diversity.rerankers.DiversityReRanker"
        ]
    },
    "logger": "recommendation.decorators.NoLogger"
}

try:
    RECOMMENDATION_SETTINGS = getattr(settings, "RECOMMENDATION_SETTINGS")
except AttributeError:
    RECOMMENDATION_SETTINGS = DEFAULT_SETTINGS


def get_class(cls):
    """
    Return a tuple with the class, a tuple with args and a dict with keyword args.
    :param cls:
    :return:
    """
    if isinstance(cls, basestring):
        cls_str, args, kwargs = cls, (), {}
    elif isinstance(cls, tuple) and isinstance(cls[0], basestring):
        if len(cls) == 2:
            if isinstance(cls[1], (tuple, list)):
                cls_str, args, kwargs = cls[0], cls[1], {}
            elif isinstance(cls[1], dict):
                cls_str, args, kwargs = cls[0], (), cls[1]
            else:
                raise AttributeError("The second element in tuple must be list, tuple or dict with python native structs.")
        elif len(cls) == 3:
            if isinstance(cls[1], (tuple, list)) and isinstance(cls[2], dict):
                cls_str, args, kwargs = cls
            else:
                raise AttributeError("The second element in tuple must be list or and the third must be dict.")
        else:
            raise AttributeError("Tuple must be size 2 or 3.")
    else:
        raise AttributeError("Attribute must be string or tuple with the first element string.")
    parts = cls_str.split(".")
    module, cls = ".".join(parts[:-1]), parts[-1]
    return getattr(__import__(module, fromlist=[""]), cls), args, kwargs


RECOMMENDATION_ENGINES = {}
log_event = None
for engine, engine_settings in RECOMMENDATION_SETTINGS.items():
    if engine != "logger":
        cls, args, kwargs = get_class(engine_settings["core"])
        RECOMMENDATION_ENGINES[engine] = cls(*args, **kwargs)

        # Register Filters
        for filter_cls in engine_settings["filters"]:
            cls, args, kwargs = get_class(filter_cls)
            RECOMMENDATION_ENGINES[engine].register_filter(cls(*args, **kwargs))

        # Register re-rankers
        for reranker_cls in RECOMMENDATION_SETTINGS["default"]["rerankers"]:
            cls, args, kwargs = get_class(reranker_cls)
            RECOMMENDATION_ENGINES[engine].register_reranker(cls(*args, **kwargs))
    else:
        cls, _, _ = get_class(engine_settings)
        log_event = cls

if not log_event:
    cls, _, _ = get_class(DEFAULT_SETTINGS["logger"])
    log_event = cls

# Set default Recommendation engine
DEFAULT_RECOMMENDATION = RECOMMENDATION_ENGINES["default"]


if __name__ == "__main__":
    import doctest
    doctest.testmod()