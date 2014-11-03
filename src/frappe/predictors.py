#! -*- unicode: utf8 -*-
"""
Predictors for the frappe recommendation system
"""

__author__ = "joaonrb"

import pandas as pd
import numpy as np
from abc import ABCMeta, abstractmethod
from frappe.decorators import Cached
from testfm.models.tensorcofi import PyTensorCoFi
from testfm.models.baseline_model import Popularity
from frappe.models import Inventory, Module, Predictor, AlgorithmData, UserFactors, User, Item


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


class TensorCoFiPredictor(IPredictor):
    """
    Predictor based on tensorCoFi algorithm
    """

    USER_MATRIX = 0
    ITEM_MATRIX = 1

    class CachedUser(object):
        """
        Cache the user matrix
        """

        def __init__(self, model):
            self._model = model

        def __getitem__(self, user_id):
            return UserFactors.get_user_factors(user_id)

        def __str__(self):
            return self._model.get_name()

    def __init__(self, predictor_id):
        self.data_map = None
        self.factors = None
        self.predictor_id = predictor_id

    @staticmethod
    def load_predictor(predictor, module):
        item_list = module.listed_items

        item_factors = predictor.data.filter(model_id=TensorCoFiPredictor.ITEM_MATRIX).order_by("-timestamp")[0]
        model = np.zeros((len(item_list), predictor.kwargs["n_factors"]), dtype=np.float32)
        for i, item in enumerate(item_list):
            try:
                model[i, :] = item_factors[item]
            except KeyError:
                pass

        algorithm = TensorCoFiPredictor(predictor.pk)
        algorithm.factors = [TensorCoFiPredictor.CachedUser(algorithm), model]
        return algorithm

    def __call__(self, user, size):
        return PyTensorCoFi.get_not_mapped_recommendation(user)

    def train(self, *args, **kwargs):
        columns = ["users", "items"]
        ivs = Inventory.objects.all().values_list("user__external_id", "item__external_id", "user_id", "item_id")
        inventory = pd.DataFrame(zip(columns, zip(*ivs)))
        data = []
        self.data_map = {}
        for column in columns:
            unique_data = inventory[column].unique()
            self.data_map[column] = pd.Series(xrange(len(unique_data)), unique_data)
            data.append(map(lambda x: self.data_map[column][x], inventory[column].values))

        data.append(inventory.get("rating", np.ones((len(inventory),)).tolist()))
        algorithm = PyTensorCoFi(*args, **kwargs)
        algorithm.train(np.array(data, dtype=np.float32).transpose())

        # Saving to the database
        users_ids = {user_eid: user_id for user_eid, i, user_id, i in ivs}
        users = {
            u.user_id: u for u in UserFactors.objects.filter(user__external_id=inventory["users"].unique())
        }
        to_save = []
        for user_eid, umid in self.data_map["users"].iteritems():
            user_id = users_ids[user_eid]
            if user_id in users:
                users[user_id].array = self.factors[0][umid]
                to_save.append(users[user_id])
            else:
                to_save.append(UserFactors(user_id=user_id, array=self.factors[0][umid]))
        UserFactors.objects.bulk_create(to_save)

        data = {}
        for item_eid, imid in self.data_map["items"].iteritems():
            data[item_eid] = self.factors[1][imid]

        d = AlgorithmData.objects.create(data=data, model_id=TensorCoFiPredictor.ITEM_MATRIX)
        Predictor.get_predictor(self.predictor_id).data.add(d)