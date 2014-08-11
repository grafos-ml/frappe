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
from django.utils.six import with_metaclass
import sys
from recommendation.decorators import PutInThreadQueue
from django.core.cache import get_cache
if sys.version_info >= (3, 0):
    basestring = unicode = str


class Matrix(with_metaclass(models.SubfieldBase, models.TextField)):
    """
    This Class is a field for the tensor matrix. It is a huge field text
    fields.

    In the Frappe backend it was called Base64Field. This is better I think.
    """

    description = """Matrix for tensor controller to find nice app suggestions"""
    __metaclass__ = models.SubfieldBase

    DECODE_MATRIX = lambda self, x: (base64.decodebytes if sys.version_info >= (3, 0) else base64.decodestring)(x)

    def to_python(self, value):
        """
        Convert the value from the database to python like object

        :param value: String from database
        :type value: str
        :return: A numpy matrix
        :rtype: numpy.Array
        """
        if isinstance(value, basestring):
            prep = bytes(value, "utf-8") if sys.version_info >= (3, 0) else bytes(value)
            return np.fromstring(self.DECODE_MATRIX(prep), dtype=np.float32)
        elif isinstance(value, bytes):
            return np.fromstring(self.DECODE_MATRIX(value), dtype=np.float32)
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


class Recommendation(with_metaclass(models.SubfieldBase, models.TextField)):
    """
    A raw recommendation based on apps that exist in the system
    """

    __metaclass__ = models.SubfieldBase

    DECODE_MATRIX = lambda self, x: (base64.decodebytes if sys.version_info >= (3, 0) else base64.decodestring)(x)

    def to_python(self, value):
        """
        Convert the string from the database to a python like object

        :param value: string of a list for a recommendation
        """
        if isinstance(value, basestring):
            prep = bytes(value, "utf-8") if sys.version_info >= (3, 0) else bytes(value)
            return np.fromstring(self.DECODE_MATRIX(prep), dtype=np.float64)
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

    @staticmethod
    def load_to_cache():
        items = {app["id"]: app for app in Item.objects.all().prefetch_related().values("id", "name", "external_id",
                                                                                        "available_locales",
                                                                                        "genres__name")}
        cache = get_cache("models")
        cache.set("recommendation_items", items, None)

    @staticmethod
    def all_items():
        """
        Get all items from cache
        """
        cache = get_cache("models")
        return cache.get("recommendation_items")


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
        Get the owned items from cache
        """
        cache = get_cache("models")
        return cache.get("user<%s>.owned_items" % self.external_id, [])

    @owned_items.setter
    def owned_items(self, value):
        cache = get_cache("models")
        items = cache.get("user<%s>.owned_items" % self.external_id, None)
        items.add(value)
        cache.set("user<%s>.owned_items" % self.external_id, items, None)

    @PutInThreadQueue()
    def save_with(self, language=None):
        """
        Save the user. If add a language if language is language model
        """
        self.save()
        if language:
            language.users.add(self)
        cache = get_cache("model")
        all_users = User.all_users()
        all_users[self.external_id] = self
        cache.set("recommendation_users", self, None)

    def get_owned_items(self):
        """
        Return the installed only apps
        """
        return self.items.filter(inventory__dropped_date=None)

    @staticmethod
    def load_owned_items():
        cache = get_cache("models")
        users = User.objects.all()
        for u in users:
            cache.set("user<%s>.owned_items" % u.external_id, list(u.get_owned_items()), None)

    @staticmethod
    def load_to_cache():
        users = {user.external_id: user for user in User.objects.all()}
        cache = get_cache("models")
        cache.set("recommendation_users", users, None)

    @staticmethod
    def all_users():
        """
        Get all items from cache
        """
        cache = get_cache("models")
        return cache.get("recommendation_users")


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
            "state": _("dropped") if self.dropped_date else _("owned"), "item": self.item.name,
            "user": self.user.external_id}

    def save(self, *args, **kwargs):
        super(Inventory, self).save(*args, **kwargs)
        cache = get_cache("models")
        cache.set("user<%s>.owned_items" % self.user.external_id, list(self.user.get_owned_items()), None)


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

    def __str__(self):
        return str(self.matrix)

    @property
    def numpy_matrix(self):
        """
        Shape the matrix in to whatever
        """
        self.matrix.shape = self.rows, self.columns
        return np.matrix(self.matrix)

    def get_type(self):
        """
        Return the type of this factor matrix
        :return: users if user factors and item otherwise
        """
        return "users" if self.dim == 0 else "items"


class PopularityModel(models.Model):
    """
    Popularity model for when there are no info on user
    """
    recommendation = Recommendation(_("recommendation"))
    number_of_items = models.IntegerField(_("number of items"))
    timestamp = models.DateTimeField(_("timestamp"), auto_now_add=True)

    class Meta:
        verbose_name = _("popularity model")
        verbose_name_plural = _("popularity models")

    def __str__(self):
        return "popularity(%s...%s)" % (str(self.recommendation[4:][:-1]), str(self.recommendation[:-4][1:]))

    def save(self, **kwargs):
        super(PopularityModel, self).save(**kwargs)
        cache = get_cache("models")
        cache.set("popularity", self, None)


from django.contrib import admin
admin.site.register([Item, User, Inventory, TensorModel, PopularityModel])

# TODO import FFPopularity to testfm