#! -*- encoding: utf-8 -*-
"""
The core module for the recommendation system. Here is defined the flow for a recommendation request and settings.
"""

__author__ = "joaonrb"

import logging
import numpy as np
import traceback
from django.conf import settings
from recommendation.models import Item, User, TensorCoFi, Popularity, Inventory
from recommendation.util import initialize
from recommendation.decorators import ContingencyProtocol
from recommendation.filter_none.filters import FilterNoneItems

try:
    RECOMMENDATION_SETTINGS = getattr(settings, "RECOMMENDATION_SETTINGS")
except AttributeError:
    from recommendation import default_settings
    RECOMMENDATION_SETTINGS = getattr(default_settings, "RECOMMENDATION_SETTINGS")

try:
    logger, _, _ = initialize(RECOMMENDATION_SETTINGS["logger"])
except KeyError:
    from recommendation.decorators import NoLogger
    logger = NoLogger()
log_event = logger


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

        >>> class Filter:
        ...     pass
        >>> controller = IController()
        >>> controller.register_filter(Filter())
        >>> print(controller.filters)  #doctest: +ELLIPSIS
        [<recommendation.core.Filter instance at 0x...>]

        :param filters: A filter to add to the controller
        """
        for f in filters:
            f.controller = self
            self._filters.append(f)

    @property
    def filters(self):
        """
        A list with all the filters registered in this controller

        >>> controller = IController()
        >>> print(controller._filters == controller.filters)
        True
        """
        return self._filters[:]

    def register_reranker(self, *rerankers):
        """
        Register a reranker for this controller.

        >>> class Reranker:
        ...     pass
        >>> controller = IController()
        >>> controller.register_reranker(Reranker())
        >>> print(controller.rerankers)  #doctest: +ELLIPSIS
        [<recommendation.core.Reranker instance at 0x...>]

        :param rerankers: A reranker to add to the controller.
        """
        for r in rerankers:
            r.controller = self
            self._re_rankers.append(r)

    @property
    def rerankers(self):
        """
        A list with all the reranker registered in this controller

        >>> controller = IController()
        >>> print(controller._re_rankers == controller.rerankers)
        True
        """
        return self._re_rankers[:]

    def get_model(self):
        """
        Catch model

        >>> class TestController(IController):
        ...     pass
        >>> TestController().get_model()
        Traceback (most recent call last):
        ...
        NotImplementedError

        :return: The Model
        """
        raise NotImplementedError()

    def get_alternative_recommendation(self, user):
        """
        Return an alternative recommendation when the first fail

        >>> class TestController(IController):
        ...     pass
        >>> TestController().get_alternative_recommendation(object())
        Traceback (most recent call last):
        ...
        NotImplementedError

        :return: list
        """
        raise NotImplementedError()

    def get_recommendation_from_model(self, user):
        """
        Get a List of significance values for each app

        >>> class TestController(IController):
        ...     pass
        >>> TestController().get_recommendation_from_model(object())
        Traceback (most recent call last):
        ...
        NotImplementedError

        :param user: The user to get the recommendation
        :return: An array with the app scores for that user
        """
        # Fix user.pk -> user.pk-1: The model was giving recommendation for the
        # previous user.
        model = self.get_model()
        try:
            return model.get_recommendation(user)  # Try to cache recommendation from tensorcofi last build.
        except (KeyError, IndexError):
            if not user.has_more_than(2):
                # Not enough items in user inventory to compute
                raise NotEnoughItemsToCompute("User %s doesn't have enough items" % user)
            apps_idx = [a.pk - 1 for a in user.owned_items.values() if a.pk - 1 <= model.factors[1].shape[0]]
            u_factors = model.online_user_factors(apps_idx)  # New factors for this user
            TensorCoFi.user_matrix[user.pk-1] = u_factors  # store new documentation in Cache
            return np.squeeze(np.asarray((u_factors * model.factors[1].transpose())))

    @log_event(log_event.RECOMMEND)
    def get_recommendation(self, user, n=10):
        """
        Method to get recommendation according with some user id

        >>> class TestController(IController):
        ...     pass
        >>> TestController().get_recommendation(user=object(), n=10)
        Traceback (most recent call last):
        ...
        NotImplementedError

        :param user: The user external_id. A way to identify the user.
        :param n: The number of recommendations to give in response.
        :return: A Python list the recommendation apps ids.
        :rtype: list
        """
        try:
            result = self.get_recommendation_from_model(user=user)
        except NotEnoughItemsToCompute:
            logging.debug(traceback.format_exc())
            result = self.get_alternative_recommendation(user)
        for f in self.filters:
            result = f(user, result, size=n)
        result = [aid for aid, _ in filter(lambda x: x[1] != float("-inf"),
                                           sorted(enumerate(result, start=1), key=lambda x: x[1], reverse=True))]
        for r in self.rerankers:
            result = r(user, result, size=n)
        return result[:n]

    @ContingencyProtocol()
    def get_external_id_recommendations(self, user, n=10):
        """
        Returns the recommendations with a list of external_is's

        >>> class TestController(IController):
        ...     pass
        >>> TestController().get_external_id_recommendations(object(), n=10)
        Traceback (most recent call last):
        ...
        NotImplementedError

        :param user: Same parameters that get_app_significance
        :param n:
        :return: Item external id list
        """
        user = User.get_user_by_external_id(user)
        result = self.get_recommendation(user=user, n=n)
        return [Item.get_item_external_id_by_id(r) for r in result]


class TensorCoFiController(IController):
    """
    Get the matrix from the Model
    """

    def get_model(self):
        """
        Catch model

        :return: The Model
        """
        return TensorCoFi.get_model_from_cache()

    def get_alternative_recommendation(self, user):
        """
        Return the popular items
        :return: list
        """
        return Popularity.get_model().recommendation


class NotEnoughItemsToCompute(Exception):
    """
    Exception for when user is short in Items to compute a new recommendation
    """
    def __init__(self, *args, **kwargs):
        super(NotEnoughItemsToCompute, self).__init__(*args, **kwargs)

RECOMMENDATION_ENGINES = {}
for engine, engine_settings in RECOMMENDATION_SETTINGS.items():
    if engine != "logger":
        cls, args, kwargs = initialize(engine_settings["core"])
        RECOMMENDATION_ENGINES[engine] = cls(*args, **kwargs)

        # Register Filters
        for filter_cls in engine_settings["filters"]:
            cls, args, kwargs = initialize(filter_cls)
            RECOMMENDATION_ENGINES[engine].register_filter(cls(*args, **kwargs))

        # Register re-rankers
        for reranker_cls in RECOMMENDATION_SETTINGS["default"]["rerankers"]:
            cls, args, kwargs = initialize(reranker_cls)
            RECOMMENDATION_ENGINES[engine].register_reranker(cls(*args, **kwargs))


# Set default Recommendation engine
default_recommendation = RECOMMENDATION_ENGINES["default"]


class ControllerNotDefined(Exception):
    """
    Exception for when controller is not defined on settings
    """
    pass


def get_controller(name="default"):
    """
    Get the recommendation controller
    :param name: The name of the controller
    :return: A controller or raise NotImplemented exception
    """
    try:
        return RECOMMENDATION_ENGINES[name]
    except KeyError:
        raise ControllerNotDefined()
