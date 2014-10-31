#! -*- unicode: utf8 -*-
"""
Predictors for the frappe recommendation system
"""

__author__ = "joaonrb"

import numpy as np
from abc import ABCMeta, abstractmethod
from frappe.decorators import Cached
from testfm.models.tensorcofi import PyTensorCoFi
from testfm.models.baseline_model import Popularity
from frappe.models import Inventory, Module, Predictor, AlgorithmData


class IPredictor(object):
    """
    Predictor interface
    """

    __metaclass__ = ABCMeta

    @staticmethod
    @abstractmethod
    def load_predictor(predictor, module):
        """
        Load a new predictor based on database info
        :param predictor: Database predictor
        :param module: Database Module
        :return: A new predictor instance
        """

    @abstractmethod
    def train(self):
        """
        Train a model based on database data. It save the module data into predictor data.
        """

    @abstractmethod
    def __call__(self, user, size):
        """
        Predict a recommendation array for user
        :param user: User requesting recommendation
        :type user: frappe.User
        :param size: The size of the recommendation
        :type size: int,>0
        :return: A numpy array with
        """


class TensorCoFiPredictor(IPredictor, PyTensorCoFi):
    """
    Predictor based on tensorCoFi algorithm
    """

    USER_MATRIX = 1
    ITEM_MATRIX = 2

    class CachedUser(object):
        """
        Cache the user matrix
        """

        def __init__(self, model):
            self._model = model

        @Cahed(lock_id=0)
        def get_user(self, user_eid):
            return self._model.factors[0]

        def __getitem__(self, item):
            return self.get_user(item)

        def __str__(self):
            return self._model.get_name()

    @staticmethod
    def load_predictor(predictor, module):
        algorithm = TensorCoFiPredictor(**predictor.kwargs)
        item_list = module.listed_items
        item_factors = predictor.data.filter(model_id=TensorCoFiPredictor.ITEM_MATRIX).order_by("-timestamp")[0]
        model = np.zeros((len(item_list), algorithm.number_of_factors))
        for i, item in enumerate(item_list):
            try:
                model[i, :] = item_factors[item]
            except KeyError:
                pass



