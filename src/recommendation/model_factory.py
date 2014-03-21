# -*- coding: utf-8 -*-
"""
.. module:: 
    :platform: 
    :synopsis: 
     3/11/14

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
from operator import itemgetter

__author__ = "joaonrb"

import os
import numpy as np
import math
import datetime
import subprocess
import recommendation
from pkg_resources import resource_filename

USER = "user"
ITEM = "item"


class TensorCoFi(object):
    """
    A creator of TensorCoFi models
    """

    def __init__(self, d=20, iterations=5, lambda_value=0.05, alpha_value=40, dimensions=[0, 0]):
        """

        :param d:
        :param iterations:
        :param lambda_value:
        :param alpha_value:
        :param dimensions:
        :return:
        """
        self.d = d
        self.dimensions = dimensions
        self.lambda_value = lambda_value
        self.alpha_value = alpha_value
        self.iterations = iterations

        self.factors = []
        self.counts = []
        for dim in dimensions:
            self.factors.append(np.random.rand(d, dim))
            self.counts.append(np.zeros((dim, 1)))
        self.regularizer = None
        self.matrix_vector_product = None
        self.one = None
        self.invertible = None
        self.tmp = None

    def iterate(self, tensor, data_array):
        """
        Iterate  over each Factor Matrix
        :param tensor:
        :return:
        """
        dimension_range = list(range(len(self.dimensions)))
        for i, dimension in enumerate(self.dimensions):

            # The base computation
            if len(self.dimensions) == 2:
                base = self.factors[1 - len(self.dimensions)]
                base = np.dot(base, base.transpose())
            else:
                base = np.ones((self.d, self.d))
                for j in dimension_range:
                    if j != i:
                        base = np.dot(self.factors[j], self.factors[j].transpose())

            if not i:  # i == 0
                for entry in range(dimension):
                    count = sum((1 for j in range(data_array.shape[0]) if data_array[j, i] == entry)) or 1
                    self.counts[i][entry, 0] = count

            for entry in range(dimension):
                if entry in tensor[i]:
                    data_row_list = tensor[i][entry]
                    for data in data_row_list:
                        self.tmp = self.tmp * 0. + 1.
                        self.tmp = self.tmp * self.factors[i][:, data_array[data, i]]
                        score = data_array[data_array.shape[1], i]
                        weight = 1. + self.alpha_value * math.log(1. + abs(score))

                        self.invertible += (1. - weight) * self.tmp * self.tmp.transpose()
                        self.matrix_vector_product += self.tmp * np.sign(score) * weight

                        self.invertible += base
                        self.regularizer = self.regularizer * 1. / self.dimensions[i]
                        self.invertible += self.regularizer

                        self.invertible = np.linalg.solve(self.invertible, self.one)

                        # Put the calculated factor back into place

                        self.factors[i][:, entry] = np.dot(self.matrix_vector_product, self.invertible)

                        # Reset invertible and matrix_vector_product
                        self.invertible *= 0.
                        self.matrix_vector_product *= 0.

    def prepare_tensor(self, data_array):
        """
        Prepare the data

        :param data_array: Data to convert in to tensor model
        """

        self.regularizer = np.multiply(np.identity(self.d), self.lambda_value)
        self.matrix_vector_product = np.zeros((1, self.d))
        self.one = np.identity(self.d)
        self.invertible = np.zeros((self.d, self.d))
        self.tmp = np.ones((1, self.d))
        tensor = {}
        for i, dim in enumerate(self.dimensions):
            tensor[i] = {}
            for j, row in enumerate(data_array):
                try:
                    tensor[i][row[0, i]].append(j)
                except KeyError:
                    tensor[i][row[0, i]] = [j]
        return tensor

    def train(self, data_array):
        """
        Implementation of TensorCoFi training in Python

        :param data_array: Data to convert in to tensor model
        """
        tensor = self.prepare_tensor(data_array)
        # Starting loops
        for _ in range(self.iterations):
            self.iterate(tensor, data_array)

    def get_model(self):
        """
        TODO
        """
        return self.factors


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

        :param d:
        :param iterations:
        :param lambda_value:
        :param alpha_value:
        :param dimensions:
        :return:
        """
        self.set_params(d, iterations, lambda_value, alpha_value)
        self.user_features = {}
        self.item_features = {}
        self.factors = {}

        self.user_column_names = user_features
        self.item_column_names = item_features

    @classmethod
    def param_details(cls):
        """
        Return parameter details for dim, nIter, lamb and alph
        """
        return {
            "dimension": (10, 20, 2, 20),
            "iteration": (1, 10, 2, 5),
            "lambda_value": (.1, 1., .1, .05),
            "alpha_value": (30, 50, 5, 40)
        }

    def fit(self, data):
        """
        Prepare the model
        """
        self._fit(data)

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

    def fit(self, data, users_len=None, items_len=None):
        directory = "log/" + datetime.datetime.now().isoformat("_")
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

    def train(self, data, **kwargs):
        return self.fit(data, **kwargs)

    def get_model(self):
        """
        TODO
        """
        return self.factors[USER], self.factors[ITEM]