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


class Matrix(models.TextField):
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
            value = value.decode('utf8')
            return np.frombuffer(base64.decodebytes(value), dtype=np.float64)
        return value

    def get_prep_value(self, value):
        """
        Prepare the value from python like object to database like value

        :param value: Matrix to keep in database
        :type value: numpy.Array
        :return: Base64 representation string encoded in utf-8
        :rtype: str
        """
        return base64.b64encode(value).encode('utf8')


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
        return self.items.filter(owned__dropped_date=None)


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


class TensorModel(models.Model):
    """
    Tensor model created with java application in lib/
    """
    dim = models.PositiveIntegerField(_('dim'))
    matrix = Matrix(_('tensor matrix'))
    rows = models.PositiveIntegerField(_('rows'))
    columns = models.PositiveIntegerField(_('columns'))

    class Meta:
        verbose_name = _('factor')
        verbose_name_plural = _('factors')

    def __unicode__(self):
        return self.matrix

    @property
    def numpy_matrix(self):
        """
        Shape the matrix in to whatever
        """
        self.matrix.shape = self.rows, self.columns
        return np.matrix(self.matrix)

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