#! -*- encoding: utf-8 -*-
"""
Models for the base of the recommendation system. The base of the recommendation system makes uses of the user, item
amd connection between them.
"""
__author__ = "joaonrb"


import sys
import base64
import numpy as np
import pandas as pd
from django.db import models
from django.utils.translation import ugettext as _
from django.core.cache import get_cache
from django.utils.six import with_metaclass
from testfm.models.tensorcofi import PyTensorCoFi
from testfm.models.baseline_model import Popularity as TestFMPopulariy
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


class Matrix(models.Model):
    """
    Numpy Matrix in database
    """

    name = models.CharField(_("name"), max_length=255)
    matrix_id = models.SmallIntegerField(_("model id"), null=True, blank=True)
    numpy = NPArray(_("numpy array"))
    timestamp = models.DateTimeField(_("timestamp"), auto_now_add=True)

    class Meta:
        verbose_name = _("matrix")
        verbose_name_plural = _("matrix")


from django.contrib import admin
admin.site.register([Item, User, Inventory, Matrix])

# Create test.fm models


class NotCached(Exception):
    """
    Exception when some value not in cache
    """
    pass


class MySQLMapDummy:
    def __getitem__(self, item):
        return int(item-1)

    def __setitem__(self, item, value):
        pass


class TensorCoFi(PyTensorCoFi):
    """
    A creator of TensorCoFi models
    """

    cache = CacheManager("tensorcofi")

    def __init__(self, n_users=None, n_items=None, **kwargs):
        """
        """
        if not isinstance(n_items, int) or not isinstance(n_users, int):
            raise AttributeError("Parameter n_items and n_users must have integer")
        super(TensorCoFi, self).__init__(**kwargs)
        self.dimensions = [n_users, n_items]
        self.n_users = n_users
        self.n_items = n_items
        self.data_map = {
            self.get_user_column(): MySQLMapDummy(),
            self.get_item_column(): MySQLMapDummy()
        }

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

    #def get_score(self, user, item):
    #    return np.dot(self.factors[0][user-1], self.factors[1][item-1].transpose())

    def get_recommendation(self, user, **context):
        """
        Get the recommendation for this user
        """
        return self.get_not_mapped_recommendation(user.pk, **context)

    @staticmethod
    def load_to_cache():
        tensor = TensorCoFi(n_users=User.objects.all().count(), n_items=Item.objects.all().count())

        try:
            users = Matrix.objects.filter(name=tensor.get_name(), model_id=0).order_by("-id")[0]
            items = Matrix.objects.filter(name=tensor.get_name(), model_id=1).order_by("-id")[0]
        except IndexError:
            raise NotCached("%s not in db" % tensor.get_name())

        tensor.factors = [users.numpy, items.numpy]
        TensorCoFi.cache[""] = tensor

    @staticmethod
    def get_model(*args, **kwargs):
        return TensorCoFi.cache[""]

    @staticmethod
    def train_from_db(*args, **kwargs):
        """
        Trains the model in to data base
        """
        tensor = TensorCoFi(n_users=User.objects.all().count(), n_items=Item.objects.all().count())
        data = np.array(sorted([(u-1, i-1) for u, i in Inventory.objects.all().values_list("user_id", "item_id")]))
        return tensor.train(data)

    def train(self, data):
        """
        Trains the model in to data base
        """
        #users, items = zip(*Inventory.objects.all().values_list("user_id", "item_id"))
        #data = pd.DataFrame({"item": users, "user": items})
        super(TensorCoFi, self).train(data)
        users, items = super(TensorCoFi, self).get_model()
        users = Matrix(name=self.get_name(), model_id=0, numpy=users)
        users.save()
        items = Matrix(name=self.get_name(), model_id=0, numpy=items)
        items.save()
        return users, items


class Popularity(TestFMPopulariy):
    """
    Popularity connector for db and test.fm
    """

    cache = CacheManager("popularity")

    def __init__(self, n_items=None, *args, **kwargs):

        if not isinstance(n_items, int):
            raise AttributeError("Parameter n_items must have integer")
        super(Popularity, self).__init__(*args, **kwargs)
        self.n_items = n_items
        self.data_map = {
            self.get_user_column(): MySQLMapDummy(),
            self.get_item_column(): MySQLMapDummy()
        }
        self.popularity_recommendation = []

    def fit(self, training_data):
        """
        Computes number of times the item was used by a user.
        :param training_data: DataFrame training data
        :return:
        """
        super(Popularity, self).fit(training_data)
        for i in range(self.n_items):
            try:
                self._counts[i+1] = self._counts[i+1]
            except KeyError:
                self._counts[i+1] = float("-inf")
        self.popularity_recommendation = [self._counts[i+1] for i in range(self.n_items)]
        self.popularity_recommendation = np.array(self.popularity_recommendation)

    #def get_score(self, user, item, **kwargs):
    #    print self._counts
    #    super(Popularity, self).get_score(user, item, **kwargs)

    @property
    def recommendation(self):
        return self.popularity_recommendation

    @recommendation.setter
    def recommendation(self, value):
        self.popularity_recommendation = value
        self._counts = {i+1: value[i] for i in range(self.n_items)}

    @staticmethod
    def load_to_cache():
        model = Popularity(n_items=Item.objects.all().count())
        pop = Matrix.objects.filter(name=model.get_name()).order_by("-id")[0]
        model.recommendation = pop.recommendation
        Popularity.cache[""] = model

    @staticmethod
    def get_model():
        return Popularity.cache[""]

    def get_recommendation(self, user, **context):
        """
        Get the recommendation for this user
        """
        return self.recommendation

    @staticmethod
    def train():
        """
        Train the popular model
        :return:
        """
        popular_model = Popularity(n_items=Item.objects.all().count())
        users, items = zip(*Inventory.objects.all().values_list("user_id", "item_id"))
        data = pd.DataFrame({"item": items, "user": users})
        popular_model.fit(data)
        Matrix.objects.create(name=popular_model.get_name(), numpy=popular_model.recommendation)
    train_from_db = train