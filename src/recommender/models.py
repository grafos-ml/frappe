# -*- coding: utf-8 -*-
"""
FireFox recommender models.

Created on Nov 28, 2013

The data module for recommendation features. Here are defined models to the
data needed for the recommendation tools.

Dome django fields are also defined here.

..moduleauthor:: joaonrb <joaonrb@gmail.com>

"""

__author__ = "joaonrb"

import os
from pkg_resources import resource_filename
os.environ['CLASSPATH'] = resource_filename(__name__, "lib/algorithm-1.0-SNAPSHOT-jar-with-dependencies.jar")
# os.environ["JAVA_OPTS"] = "-Xmx4096M"
from django.db import models
from django.utils.translation import ugettext as _
import base64
import numpy as np
import math
from django.utils.six import with_metaclass


class Matrix(with_metaclass(models.SubfieldBase, models.TextField)):
    """
    This Class is a field for the tensor matrix. It is a huge field text
    fields.

    In the Frappe backend it was called Base64Field. This is better I think.
    """

    description = """Matrix for tensor controller to find nice app suggestions"""
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """
        Convert the value from the database to python like object

        :param value: String from database
        :type value: str
        :return: A numpy matrix
        :rtype: numpy.Array
        """
        if isinstance(value, str):
            prep = bytes(value, "utf-8")
            return np.fromstring(base64.decodebytes(prep), dtype=np.float64)
        return value

    def get_prep_value(self, value):
        """
        Prepare the value from python like object to database like value

        :param value: Matrix to keep in database
        :type value: numpy.Array
        :return: Base64 representation string encoded in utf-8
        :rtype: str
        """
        prep = value.tostring()
        return base64.b64encode(prep)


class Item(models.Model):
    """
    Item to be used by recommending system
    """
    name = models.CharField(_("name"), max_length=255)
    external_id = models.CharField(_("external id"), max_length=255, unique=True)

    class Meta:
        verbose_name = _("item")
        verbose_name_plural = _("items")

    def __str__(self):
        return self.name


class User(models.Model):
    """
    User to own items in recommendation system
    """
    external_id = models.CharField(_("external id"), max_length=255, unique=True)
    items = models.ManyToManyField(Item, verbose_name=_("items"), blank=True, through="Inventory")

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.external_id

    @property
    def owned_items(self):
        """
        Return the installed only apps
        """
        return self.items.filter(inventory__dropped_date=None)


class Inventory(models.Model):
    """
    The connection between the user and the item. It has information about the user and the item such as acquisition
    date and eventually the date in which the item is dropped.
    """
    user = models.ForeignKey(User, verbose_name=_("user"))
    item = models.ForeignKey(Item, verbose_name=_("item"))
    acquisition_date = models.DateTimeField(_("acquisition date"))
    dropped_date = models.DateTimeField(_("dropped date"), null=True, blank=True)

    class Meta:
        verbose_name = _("owned item")
        verbose_name_plural = _("owned items")
        unique_together = ("user", "item")

    def __str__(self):
        return _("%(state)s %(item)s item for user %(user)s") % {
            "state": _("dropped") if self.removed_date else _("owned"), "item": self.item.name,
            "user": self.user.external_id}


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
                        base = self.factors[j] * self.factors[j].transpose()

            if not i:  # i == 0
                for entry in range(dimension):
                    count = sum((1 for j in range(data_array.shape[0]) if data_array[j, i] == entry)) or 1
                    self.counts[i][entry, 0] = count

            for entry in range(dimension):
                if entry in tensor[i]:
                    data_row_list = tensor[i][entry].tolist()[0]
                    for data_column, data in enumerate(data_row_list):
                        self.tmp = self.tmp * 0. + 1.
                        if data_column != i:
                            self.tmp = self.tmp * self.factors[data_column][:, data]
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
            for row in data_array:
                tensor[i][row[0, i]] = row
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


class TensorModel(models.Model):
    """
    Tensor model created with java application in lib/
    """
    dim = models.PositiveIntegerField(_("dim"))
    matrix = Matrix(_("tensor matrix"))
    rows = models.PositiveIntegerField(_("rows"))
    columns = models.PositiveIntegerField(_("columns"))

    class Meta:
        verbose_name = _("factor")
        verbose_name_plural = _("factors")

    def __unicode__(self):
        return self.matrix

    @property
    def numpy_matrix(self):
        """
        Shape the matrix in to whatever
        """
        self.matrix.shape = self.rows, self.columns
        return np.matrix(self.matrix)

    @staticmethod
    def train():
        """
        TODO
        """
        data = Inventory.objects.all().order_by("user").values_list("user", "item")
        np_data = np.matrix([(u-1, i-1) for u, i in data])
        tensor = TensorCoFi(dimensions=[len(User.objects.all()), len(Item.objects.all())])
        tensor.train(np_data)
        users, items = tensor.get_model()

        users = TensorModel(matrix=users, rows=users.shape[0], columns=users.shape[1], dim=0)
        users.save()
        items = TensorModel(matrix=items, rows=items.shape[0], columns=items.shape[1], dim=1)
        items.save()
        return users, items


    '''
    @staticmethod
    def train():
        """
        Builds a new tensor matrix for recommendation
        """
        from jnius import autoclass
        JavaTensorCoFi = autoclass('es.tid.frappe.recsys.TensorCoFi')
        MySQLDataReader = autoclass('es.tid.frappe.mysql.MySQLDataReader')
        reader = MySQLDataReader(settings.DATABASES['default']['HOST'], 3306,
                                 settings.DATABASES['default']['TEST_NAME' if settings.TESTING else 'NAME'],
                                 settings.DATABASES['default']['USER'], settings.DATABASES['default']['PASSWORD'])

        tensor = JavaTensorCoFi(20, 5, 0.05, 40, [len(FFOSUser.objects.all()), len(FFOSApp.objects.all())])
        data = reader.getData()
        tensor.train(data)

        # Put model in database
        final_model = tensor.getModel()

        users = TensorModel._float_matrix2numpy(final_model.get(0))
        items = TensorModel._float_matrix2numpy(final_model.get(1))

        TensorModel.objects.create(matrix=users, rows=users.shape[0], columns=users.shape[1], dim=0)
        TensorModel.objects.create(matrix=items, rows=items.shape[0], columns=items.shape[1], dim=1)
        return users, items

    @staticmethod
    def _float_matrix2numpy(java_float_matrix):
        """
        Java Float Matrix is a 1-D array writen column after column.
        Numpy reads row after row, therefore, we need a conversion.
        """
        columns_input = java_float_matrix.toArray()
        split = lambda lst, sz: [np.fromiter(lst[i:i+sz], dtype=np.float) for i in xrange(0, len(lst), sz)]
        cols = split(columns_input, java_float_matrix.rows)
        matrix = np.ma.column_stack(cols)
        return matrix

    '''

#class PopularItems(models.Model):
#    """
#    Popular items storage periodically te popular
#    """
#    timestamp = models.DateTimeField(_("timestamp"), auto_now_add=True)
#
#    class Meta:
#        verbose_name = _("popular items")
#        verbose_name_plural = _("popular items")
#
#    def __str__(self):
#        return self.timestamp.strftime()

from django.contrib import admin
admin.site.register([Item, User, Inventory, TensorModel])