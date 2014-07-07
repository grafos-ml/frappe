# -*- coding: utf-8 -*-
"""
.. module::
    :platform:
    :synopsis:
     3/11/14

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""

__author__ = "joaonrb"

import os
import numpy as np
import datetime
import subprocess
import recommendation
from pkg_resources import resource_filename
import shutil
from django.db.models import Count
from testfm.models.tensorcofi import PyTensorCoFi

USER = "user"
ITEM = "item"


class TensorCoFi(PyTensorCoFi):
    """
    A creator of TensorCoFi models
    """

    def __init__(self, n_users=None, n_items=None, **kwargs):
        """
        """
        if not isinstance(n_items, int) or not isinstance(n_users, int):
            raise AttributeError("Parameter n_items and n_users must have integer")
        super(TensorCoFi, self).__init__(**kwargs)
        self.n_users = n_users
        self.n_items = n_items

    def users_size(self):
        """
        Return the number of users
        """
        return self.n_users

    def items_size(self):
        """
        Return the number of items
        """
        return self.n_items


class JavaTensorCoFi(object):
    """
    Loads the tensor from the database based on file exchange
    """

    _d = None
    _iterations = None
    _lambda_value = None
    _alpha_value = None

    def __init__(self, d=20, iterations=5, lambda_value=0.05, alpha_value=40, user_features=["user"],
                 item_features=["item"]):
        """
        Constructor
        :param d: Number of factors
        :param iterations: Number of iterations
        :param lambda_value: Constant lambda
        :param alpha_value: Constant alpha
        :return:
        """
        self.set_params(d, iterations, lambda_value, alpha_value)
        self.user_features = {}
        self.item_features = {}
        self.factors = {}

        self.user_column_names = user_features
        self.item_column_names = item_features

    def set_params(self, d=20, iterations=5, lambda_value=0.05, alpha_value=40):
        """
        Set the parameters for the TensorCoFi

        :param d: The number of
        :param iterations: The number of iterations the algorithm should perform
        :param lambda_value: Lambda constant for the algorithm
        :param alpha_value: Alpha constant for this algorithm
        """
        self._d = d
        self._iterations = iterations
        self._lambda_value = lambda_value
        self._alpha_value = alpha_value

    def get_name(self):
        """
        toString kind
        :return:
        """
        return "TensorCoFi(d={},iterations={},lambda={},alpha={})".format(
            self._d, self._iterations, self._lambda_value, self._alpha_value)

    def fit(self, data, users_len=None, items_len=None, remove_log=True):
        """
        Trains the model with a set of data

        :param data: Data to train the model
        :param users_len: The number of users
        :param items_len: The number of items
        :param remove_log: If it should remove the log after the execution
        """
        directory = resource_filename(__name__, "/tensorcofi_log/") + datetime.datetime.now().isoformat("_")
        users_len = users_len or len(set(row[0, 0] for row in data))
        items_len = items_len or len(set(row[0, 1] for row in data))
        if not os.path.exists(directory):
            os.makedirs(directory)
        np.savetxt(directory+"/train.csv", data, delimiter=", ", fmt="%d")
        name = directory+"/"
        sub = subprocess.Popen(["java", "-cp",
                                resource_filename(recommendation.__name__,
                                                  "lib/algorithm-1.0-SNAPSHOT-jar-with-dependencies.jar"),
                                "es.tid.frappe.python.TensorCoPy", name, str(self._d), str(self._iterations),
                                str(self._lambda_value), str(self._alpha_value), str(users_len), str(items_len)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = sub.communicate()
        if err:
            raise Exception(err)
        users, items = out.decode("utf-8").split(" ")
        self.factors = {
            'user': np.ma.column_stack(np.loadtxt(open(users, "r"), delimiter=",")).transpose(),
            'item': np.ma.column_stack(np.loadtxt(open(items, 'r'), delimiter=",")).transpose()
        }
        if remove_log:
            shutil.rmtree(resource_filename(__name__, "/tensorcofi_log/"))

    def train(self, data, **kwargs):
        """
        Trains the data
        :param data:
        :param kwargs:
        :return:
        """
        return self.fit(data, **kwargs)

    def get_model(self):
        """
        Return the user matrix and item matrix as a tuple
        """
        return self.factors[USER], self.factors[ITEM]


class Popularity(object):
    """
    Popularity model for when there no user information
    """

    @staticmethod
    def get_popular_items(model):
        """
        Get the popular items in the system
        """
        items = model.objects.all().annotate(count=Count("user")).values_list("id", "count")
        sorted_items = sorted(items, key=lambda x: x[0])
        recommendation = [count for _, count in sorted_items]
        return np.array(recommendation)

    @staticmethod
    def get_name():
        """
        toSting like
        """
        return "Popularity"