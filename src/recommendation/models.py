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
from django.db.models.signals import post_save
from django.dispatch import receiver
from testfm.models.tensorcofi import PyTensorCoFi
from testfm.models.baseline_model import Popularity as TestFMPopularity
from recommendation.decorators import GoToThreadQueue
if sys.version_info >= (3, 0):
    basestring = unicode = str


class NPArrayField(with_metaclass(models.SubfieldBase, models.TextField)):
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
            shape, matrix = rest[:dim], np.fromstring(self.DECODE_MATRIX(":".join(rest[dim:])), dtype=np.float32)
            matrix.shape = tuple(int(i) for i in shape)
            return matrix
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
        self._list = "%s.list" % prefix
        self._cache.set(self._list, self._cache.get(self._list) or set([]), None)

    def __getitem__(self, key):
        k = "%s%s" % (self._prefix, key)
        result = self._cache.get(k)
        if result is None:
            raise KeyError(k)
        return result

    def __setitem__(self, key, value):
        k = "%s%s" % (self._prefix, key)
        keys = self._cache.get(self._list)
        keys.add(k)
        self._cache.set(self._list, keys, None)
        self._cache.set(k, value, None)

    def __iter__(self):
        return iter(self._cache.get_many(list(self._cache.get(self._list))).values())

    def __len__(self):
        return len(self._cache.get(self._list))

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
    #    super(IRecommendationModel, self).save(*args, **kwargs)


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

    def __unicode__(self):
        return unicode(self.name)

    @staticmethod
    def load_to_cache():
        for app in Item.objects.all().prefetch_related():
            Item.item_by_id[app.pk] = app
            Item.item_by_external_id[app.external_id] = app


@receiver(post_save, sender=Item)
def add_item_to_cache(sender, instance, created, raw, using, update_fields, *args, **kwargs):
    """
    Add item to cache upon creation
    """
    if created:
        Item.item_by_id[instance.pk] = instance
        Item.item_by_external_id[instance.external_id] = instance


class User(models.Model):
    """
    User to own items in recommendation system.
    """
    external_id = models.CharField(_("external id"), max_length=255, unique=True)
    items = models.ManyToManyField(Item, verbose_name=_("items"), blank=True, through="Inventory")

    user_by_id = CacheManager("recusid")
    user_by_external_id = CacheManager("recusei")
    __user_items = CacheManager("recusit")

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.external_id

    def __unicode__(self):
        return unicode(self.external_id)

    @property
    def all_items(self):
        """
        All items from this user. Key item id and value the inventory register
        """
        return {k: v for k, v in User.__user_items[self.pk].items()}

    @property
    def owned_items(self):
        """
        Get the owned items from cache. Key item id and value the inventory register
        """
        return {k: v for k, v in User.__user_items[self.pk].items() if v.dropped_date is None}

    @staticmethod
    def load_to_cache():
        for user in User.objects.all():
            user.load_user()

    def load_user(self):
        """
        Load a single user to cache
        """
        User.user_by_id[self.pk] = self
        User.user_by_external_id[self.external_id] = self
        user_items = self.__user_items.get(self.pk, {})
        for item in Inventory.objects.filter(user=self):
            user_items[item.item.pk] = item
        self.__user_items[self.pk] = user_items

    def load_item(self, item):
        """
        Load a single item to inventory
        """
        user_items = self.__user_items.get(self.pk, {})
        user_items[item.item.pk] = item
        self.__user_items[self.pk] = user_items


@receiver(post_save, sender=User)
def add_user_to_cache(sender, instance, created, raw, using, update_fields, *args, **kwargs):
    """
    Add item to cache upon creation
    """
    if created:
        instance.load_user()


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

    def __unicode__(self):
        return _("%(state)s %(item)s item for user %(user)s") % {
            "state": _("dropped") if self.dropped_date else _("owned"), "item": self.item.name,
            "user": self.user.external_id}


@receiver(post_save, sender=Inventory)
def add_inventory_to_cache(sender, instance, created, raw, using, update_fields, *args, **kwargs):
    """
    Add item to cache upon creation
    """
    if created:
        instance.user.load_item(instance)


class Matrix(models.Model):
    """
    Numpy Matrix in database
    """

    name = models.CharField(_("name"), max_length=255)
    matrix_id = models.SmallIntegerField(_("model id"), null=True, blank=True)
    numpy = NPArrayField(_("numpy array"))
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

    def get_score(self, user, item):
        #print self.factors[0].shape, self.factors[1].shape
        #try:
        return np.dot(self.factors[0][self.data_map[self.get_user_column()][user]],
                      self.factors[1][self.data_map[self.get_item_column()][item]].transpose())
        #except Exception as e:
        #    print user, item, self.factors[0].shape, self.factors[1].shape, len(self.factors)
        #    raise e
        #return super(TensorCoFi, self).get_score(int(user), int(item))

    def get_recommendation(self, user, **context):
        """
        Get the recommendation for this user
        """
        return self.get_not_mapped_recommendation(user.pk, **context)

    @staticmethod
    def load_to_cache():
        tensor = TensorCoFi(n_users=User.objects.all().count(), n_items=Item.objects.all().count())

        try:
            users = Matrix.objects.filter(name=tensor.get_name(), matrix_id=0).order_by("-id")[0]
            items = Matrix.objects.filter(name=tensor.get_name(), matrix_id=1).order_by("-id")[0]
        except IndexError:
            raise NotCached("%s not in db" % tensor.get_name())

        tensor.factors = [users.numpy, items.numpy]
        TensorCoFi.cache[""] = tensor

    @staticmethod
    def get_model_from_cache(*args, **kwargs):
        return TensorCoFi.cache[""]

    @staticmethod
    def get_model(*args, **kwargs):
        return TensorCoFi.get_model_from_cache(args, **kwargs).factors

    @staticmethod
    def train_from_db(*args, **kwargs):
        """
        Trains the model in to data base
        """
        #data = map(lambda x: {"user": x["user_id"], "item": x["item_id"]},
        #           Inventory.objects.all().values("user_id", "item_id"))
        #data = pd.DataFrame(data)
        tensor = TensorCoFi(n_users=User.objects.all().count(), n_items=Item.objects.all().count())
        data = np.array(sorted([(u-1, i-1, 1.) for u, i in Inventory.objects.all().values_list("user_id", "item_id")]))
        return tensor.train(data)

    def train(self, data):
        """
        Trains the model in to data base
        """
        #users, items = zip(*Inventory.objects.all().values_list("user_id", "item_id"))
        #data = pd.DataFrame({"item": users, "user": items})
        super(TensorCoFi, self).train(data)
        users, items = super(TensorCoFi, self).get_model()
        users = Matrix(name=self.get_name(), matrix_id=0, numpy=users)
        users.save()
        items = Matrix(name=self.get_name(), matrix_id=1, numpy=items)
        items.save()
        return users, items


class Popularity(TestFMPopularity):
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
        return np.array(self.popularity_recommendation).astype(np.float32)

    @recommendation.setter
    def recommendation(self, value):
        self.popularity_recommendation = value.tolist()
        self._counts = {i+1: value[i] for i in range(self.n_items)}

    @staticmethod
    def load_to_cache():
        model = Popularity(n_items=Item.objects.all().count())
        pop = Matrix.objects.filter(name=model.get_name()).order_by("-id")[0]
        model.recommendation = pop.numpy
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