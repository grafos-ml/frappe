#! -*- encoding: utf-8 -*-
"""
Models for the base of the recommendation system. The base of the recommendation system makes uses of the user, item
amd connection between them.
"""
__author__ = "joaonrb"


from django.db import models
from django.utils.translation import ugettext as _
import base64
import numpy as np
from django.utils.six import with_metaclass
import sys
from django.core.cache import get_cache
if sys.version_info >= (3, 0):
    basestring = unicode = str


class NPArray(with_metaclass(models.SubfieldBase, models.TextField)):
    """
    Numpy Array field to store numpy arrays in database

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
            value = bytes(value, "utf-8") if sys.version_info >= (3, 0) else bytes(value)
        if isinstance(value, bytes):
            parts = value.split(":")
            dim, rest = int(parts[0]), parts[1:]
            shape, matrix = rest[:dim], rest[dim:]
            return np.fromstring(self.DECODE_MATRIX(matrix), dtype=np.float32)
        return value

    def get_prep_value(self, value):
        """
        Prepare the value from python like object to database like value

        :param value: Matrix to keep in database
        :type value: numpy.Array
        :return: Base64 representation string encoded in utf-8
        :rtype: str
        """
        return ":".join([str(len(value.shape)), ":".join(map(lambda x: str(x), value.shape)),
                         base64.b64encode(value.tostring())])


class CacheManager(object):
    """
    An iterable structure that holds in the settings default cache to keep for fast access.
    """

    def __init__(self, prefix, cache="default"):
        self._cache = get_cache(cache)
        self._prefix = prefix
        self._cache.set(self._prefix, [], None)

    def __getitem__(self, key):
        k = "%s%s" % (self._prefix, key)
        result = self._cache.get(k)
        if result is None:
            raise KeyError(k)
        return result

    def __setitem__(self, key, value):
        k = "%s%s" % (self._prefix, key)
        self._cache.set(k, value, None)
        self._cache.get(self._prefix).append(value)  # TODO Test this

    def __iter__(self):
        return (i for i in self._cache.get(self._prefix))

    def __len__(self):
        return len(self._cache.get(self._prefix))


class Item(models.Model):
    """
    Item to be used by recommending system
    """
    name = models.CharField(_("name"), max_length=255)
    external_id = models.CharField(_("external id"), max_length=255, unique=True)

    # Cache Managers

    item_by_id = CacheManager("recitid")
    item_by_external_id = CacheManager("recitei")

    class Meta:
        verbose_name = _("item")
        verbose_name_plural = _("items")

    def __str__(self):
        return self.name

    @staticmethod
    def load_to_cache():
        for app in Item.objects.all().prefetch_related():
            Item.item_by_id[app.pk] = app
            Item.item_by_external_id[app.external_id] = app


class User(models.Model):
    """
    User to own items in recommendation system.
    """
    external_id = models.CharField(_("external id"), max_length=255, unique=True)
    items = models.ManyToManyField(Item, verbose_name=_("items"), blank=True, through="Inventory")

    user_by_id = CacheManager("recusid")
    user_by_external_id = CacheManager("recusei")
    __user_items = CacheManager("recusit")
    __user_owned_items = CacheManager("recusoit")

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.external_id

    @property
    def all_items(self):
        """
        All items from this user
        """
        return {i: Item.item_by_id[i] for i in User.__user_items[self.pk]}

    @property
    def owned_items(self):
        """
        Get the owned items from cache
        """
        return {i: Item.item_by_id[i] for i in User.__user_owned_items[self.pk]}

    @staticmethod
    def load_to_cache():
        for user in User.objects.all():
            User.user_by_id[user.pk] = user
            User.user_by_external_id[user.external_id] = user
            user.__user_items[user.pk] = []
            user.__user_owned_items[user.pk] = []
            for item in user.items.all():
                user.__user_items[user.pk].append(item.pk)
                if item.inventory.dropped_date is None:
                    user.__user_owned_items[user.pk].append(item.pk)


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