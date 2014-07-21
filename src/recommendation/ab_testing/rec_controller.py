#! -*- encoding: utf -*-
__author__ = 'joaonrb'

from recommendation.core import IController
from recommendation.model_factory import TensorCoFi, Popularity
from recommendation.caches import CacheUser
from recommendation.ab_testing.decorators import ABLogger
import random
import numpy as np


class IPicker(object):
    """
    Model piker for the A/B testing
    """

    def get_model(self, user):
        """
        Returns a tuple with the model position in the queue and the model. The mode position is useful to identify the
        A model with the B model and eventually C, D, etc...
        """
        raise NotImplemented


class UniformPicker(IPicker):
    """
    Random picker based on uniform distribution
    """

    def __init__(self, *model_set):
        self.__models = list(enumerate(model_set[:], start=1))

    def get_model(self, user):
        """
        Return one of the models based on the uniform
        :param user: A recommendation. User that may influence in the piking.
        :return: One model
        """
        return random.choice(self.__models)


class ABTesting(IController):

    def __init__(self, picker=None, *args, **kwargs):
        """
        Constructor. May receive a
        :param args:
        :param kwargs:
        :return:
        """
        super(ABTesting, self).__init__(*args, **kwargs)
        if picker:
            if not isinstance(picker, IPicker):
                raise TypeError("The picker parameter must be an instance of IPicker or None")
            self.__picker = picker
        else:
            self.__picker = UniformPicker(Popularity, TensorCoFi)

    def get_model(self, user):
        """
        Catch model from the picker

        :return: The Model
        """
        pos, model = self.__picker.get_model(user)
        return pos, model.get_model()

    def get_alternative(self, user):
        """
        Return the popular items
        :return: list
        """
        model = Popularity.get_model()
        return 0, model, model.recommendation

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
        pos, model = self.get_model(user)
        if user.pk-1 >= model.factors[0].shape[0]:  # We have a new user, so lets construct factors for him:
            apps_idx = [a.pk - 1 for a in user.owned_items if a.pk - 1 <= model.factors[1].shape[0]]
            if len(apps_idx) < 3:
                raise ValueError
            u_factors = model.online_user_factors(apps_idx)
            return pos, model, np.squeeze(np.asarray((u_factors * model.factors[1].transpose())))
        else:
            return pos, model, model.get_recommendation(user)

    @CacheUser()
    @ABLogger()
    def get_recommendation(self, user, n=10):
        """
        Method to get recommendation according with some user id

        :param user: The user external_id. A way to identify the user.
        :param n: The number of recommendations to give in response.
        :return: A Python list the recommendation apps ids.
        :rtype: list
        """
        try:
            pos, model, result = self.get_recommendation_from_model(user=user)
        except Exception:
            print("Wild error appear in core recommendation")
            pos, model, result = self.get_alternative(user)
        for f in self.filters:
            result = f(user, result, size=n)
        result = [aid+1 for aid, _ in sorted(enumerate(result), key=lambda x: x[1], reverse=True)]
        for r in self.rerankers:
            result = r(user, result, size=n)
        return pos, model, result[:n]
        #return self.run_re_rankers(recommendation=list(enumerate(result, start=1)), n=n)

