# -*- coding: utf-8 -*-
"""
FireFox recommendation models.

Created on Nov 28, 2013

The data module for recommendation features. Here are defined models to the
data needed for the recommendation tools.

Dome django fields are also defined here.

..moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"


from django.db import models
from django.utils.translation import ugettext as _
import base64
import numpy as np
from recommendation.model_factory import JavaTensorCoFi
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
        np_data = np.matrix([(u, i) for u, i in data])
        tensor = JavaTensorCoFi()
        tensor.train(np_data, users_len=len(User.objects.all()), items_len=len(Item.objects.all()))
        users, items = tensor.get_model()
        users = TensorModel(matrix=users, rows=users.shape[0], columns=users.shape[1], dim=0)
        users.save()
        items = TensorModel(matrix=items, rows=items.shape[0], columns=items.shape[1], dim=1)
        items.save()
        return users, items

from django.contrib import admin
admin.site.register([Item, User, Inventory, TensorModel])