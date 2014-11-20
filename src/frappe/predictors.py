#! -*- unicode: utf8 -*-
"""
Predictors for the frappe recommendation system
"""

__author__ = "joaonrb"

import logging
import pandas as pd
import numpy as np
from abc import ABCMeta, abstractmethod
from django.db import OperationalError
from testfm.models.tensorcofi import PyTensorCoFi
from testfm.models.baseline_model import Popularity
from frappe.models import Inventory, Predictor, AlgorithmData, UserFactors


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
    def train(self, *args, **kwargs):
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


class PopularityPredictor(IPredictor):
    """
    Predictor based on popularity algorithm
    """
    def __init__(self, predictor_id, model=None):
        self.model = model
        self.predictor_id = predictor_id

    @staticmethod
    def load_predictor(predictor, module):
        try:
            item_factors = predictor.data.all().order_by("-timestamp")[0].data
        except IndexError:
            model = None
        else:
            model = np.zeros((len(module.listed_items)), np.float32)
            for i, item in enumerate(module.listed_items):
                try:
                    model[i] = item_factors[item]
                except KeyError:
                    pass

        algorithm = PopularityPredictor(predictor.pk, model)
        return algorithm

    def __call__(self, user, size):
        return self.model

    def train(self, *args, **kwargs):
        columns = ["user", "item", "item_id"]
        ivs = Inventory.objects.all().values_list("user__external_id", "item__external_id", "item_id")
        inventory = pd.DataFrame(dict(zip(columns, zip(*ivs))))
        data_map = inventory["item"].unique()
        Popularity.get_counts = lambda self: self._counts

        algorithm = Popularity(*args, **kwargs)
        algorithm.fit(inventory)
        # Save to database
        data = {}
        for item_eid in data_map:
            try:
                data[item_eid] = algorithm.get_counts()[item_eid]
            except KeyError:
                pass
        self.model = data
        d = AlgorithmData.objects.create(data=data, predictor_id=self.predictor_id)
        Predictor.get_predictor(self.predictor_id).data.add(d)


class CachedUser(object):
    """
    Cache the user matrix
    """

    def __getitem__(self, user_id):
        return UserFactors.get_user_factors(user_id).array


class TensorCoFiPredictor(IPredictor):
    """
    Predictor based on tensorCoFi algorithm
    """

    USER_MATRIX = 0
    ITEM_MATRIX = 1

    def __init__(self, predictor_id):
        self.factors = None
        self.predictor_id = predictor_id
        self.__inventory__ = None

    @staticmethod
    def load_predictor(predictor, module):
        try:
            item_factors = predictor.data.filter(model_id=TensorCoFiPredictor.ITEM_MATRIX).order_by("-timestamp")[0]
        except IndexError:
            model = None
        else:
            model = np.zeros((len(module.listed_items), predictor.kwargs.get("n_factors", 20)), dtype=np.float32)
            for i, item in enumerate(module.listed_items):
                try:
                    model[i, :] = item_factors.data[item]
                except KeyError:
                    pass
        algorithm = TensorCoFiPredictor(predictor.pk)
        algorithm.factors = [CachedUser(), model]
        return algorithm

    def __call__(self, user, size):
        users, items = self.factors
        return np.squeeze(np.asarray(np.dot(users[user.pk], items.transpose())))

    def get_training(self):
        columns = ["user", "item", "user_id", "item_id"]
        UserFactors.objects.all().delete()
        self.__inventory__ = Inventory.objects.all().values_list("user__external_id", "item__external_id", "user_id", "item_id")
        return pd.DataFrame(dict(zip(columns, zip(*self.__inventory__))))

    def train(self, *args, **kwargs):
        algorithm = PyTensorCoFi(*args, **kwargs)
        algorithm.fit(self.get_training())

        # Saving to the database
        users_ids = {user_eid: user_id for user_eid, i, user_id, i in self.__inventory__}
        to_save = []
        for user_eid, umid in algorithm.data_map["user"].iteritems():
            user_id = users_ids[user_eid]
            to_save.append(UserFactors(user_id=user_id, array=algorithm.factors[0][umid]))
        try:
            UserFactors.objects.bulk_create(to_save)
        except OperationalError:
            logging.warn("To many user factors to bulk insertion. MySQL query allow 16MB per query by default.")
            logging.info("Trying to break query in chunks")
            for i in range(0, len(to_save), 250):
                UserFactors.objects.bulk_create(to_save[i:i+250])

        data = {}
        for item_eid, imid in algorithm.data_map["item"].iteritems():
            data[item_eid] = algorithm.factors[1][imid]

        d = AlgorithmData.objects.create(data=data, model_id=TensorCoFiPredictor.ITEM_MATRIX,
                                         predictor_id=self.predictor_id)
        Predictor.get_predictor(self.predictor_id).data.add(d)