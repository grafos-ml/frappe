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
import functools
try:
    from uwsgidecorators import lock
except Exception:
    lock = lambda x: x
#lock = lambda x: x
from django.db import models
from django.utils.translation import ugettext as _
from django.utils.six import with_metaclass
from django.core.cache import get_cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from testfm.models.tensorcofi import PyTensorCoFi
from testfm.models.baseline_model import Popularity as TestFMPopularity
if sys.version_info >= (3, 0):
    basestring = unicode = str
from recommendation.decorators import Cached


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

    def __getitem__(self, key):
        k = "%s%s" % (self._prefix, key)
        result = self._cache.get(k)
        if result is None:
            raise KeyError(k)
        return result

    #@functools.wraps(lock)
    def __setitem__(self, key, value):
        k = "%s%s" % (self._prefix, key)
        self._cache.set(k, value, None)

    #@functools.wraps(lock)
    def __delitem__(self, key):
        k = "%s%s" % (self._prefix, key)
        self._cache.delete(k)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


class IterableCacheManager(CacheManager):
    """
    An iterable structure that holds in the settings default cache to keep for fast access.
    """

    def __init__(self, prefix, cache="default"):
        super(IterableCacheManager, self).__init__(prefix, cache)
        self._list = "%s.list" % prefix
        self._cache.set(self._list, self._cache.get(self._list) or set([]), None)

    def __getitem__(self, key):
        k = "%s%s" % (self._prefix, key)
        result = self._cache.get(k)
        if result is None:
            raise KeyError(k)
        return result

    #@functools.wraps(lock)
    def __setitem__(self, key, value):
        k = "%s%s" % (self._prefix, key)
        # This might need a lock
        keys = self._cache.get(self._list)
        keys.add(k)
        self._cache.set(self._list, keys, None)
        #########################
        self._cache.set(k, value, None)

    #@functools.wraps(lock)
    def __delitem__(self, key):
        # TODO Test of this
        k = "%s%s" % (self._prefix, key)
        # This might need a lock
        keys = self._cache.get(self._list)
        keys.remove(k)
        self._cache.set(self._list, keys, None)
        #########################
        self._cache.delete(k)

    def __iter__(self):
        return iter(self._cache.get_many(list(self._cache.get(self._list))).values())

    def __len__(self):
        return len(self._cache.get(self._list))


class Item(models.Model):
    """
    Item to be used by recommending system
    """
    name = models.CharField(_("name"), max_length=255)
    external_id = models.CharField(_("external id"), max_length=255, unique=True)

    @staticmethod
    def get_item_by_id(item_id):
        """
        Return item by id
        """
        return Item.get_item_by_external_id(Item.get_item_external_id_by_id(item_id))

    @staticmethod
    @Cached()
    def get_item_external_id_by_id(item_id):
        """
        Return item id from external_id
        """
        return Item.objects.filter(pk=item_id).values_list("external_id")[0][0]

    @staticmethod
    @Cached()
    def get_item_by_external_id(external_id):
        """
        Return item from external id
        """
        return Item.objects.get(external_id=external_id)

    @functools.wraps(lock)
    def put_item_to_cache(self):
        """
        Loads an app to database
        """
        cache = get_cache("default")
        cache.set("%s_%s" % (Item.get_item_by_external_id.__name__, self.external_id), self, None)
        cache.set("%s_%s" % (Item.get_item_external_id_by_id.__name__, self.pk), self.external_id, None)

    @functools.wraps(lock)
    def del_item_from_cache(self):
        """
        delete an app to database
        """
        cache = get_cache("default")
        cache.delete("%s_%s" % (Item.get_item_by_external_id.__name__, self.external_id))
        cache.delete("%s_%s" % (Item.get_item_external_id_by_id.__name__, self.pk))

    class Meta:
        verbose_name = _("item")
        verbose_name_plural = _("items")

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.name)

    @staticmethod
    def load_to_cache():
        for item in Item.objects.all().prefetch_related():
            item.put_item_to_cache()


@receiver(post_save, sender=Item)
def add_item_to_cache(sender, instance, created, raw, using, update_fields, *args, **kwargs):
    """
    Add item to cache upon creation
    """
    instance.put_item_to_cache()


@receiver(post_delete, sender=Item)
def delete_item_to_cache(sender, instance, using, **kwargs):
    """
    Add item to cache upon creation
    """
    instance.del_item_from_cache()


class User(models.Model):
    """
    User to own items in recommendation system.
    """
    external_id = models.CharField(_("external id"), max_length=255, unique=True)
    items = models.ManyToManyField(Item, verbose_name=_("items"), blank=True, through="Inventory")

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.external_id

    def __unicode__(self):
        return unicode(self.external_id)

    @staticmethod
    @Cached()
    def get_user_by_id(user_id):
        """
        Get user by their id
        :param user_id: User id
        :return: A user instance
        """
        return User.objects.get(pk=user_id)

    @staticmethod
    @Cached()
    def get_user_id_by_external_id(external_id):
        """
        Get the user id from external id
        :param external_id: User external id
        :return: The user id
        """
        return User.objects.filter(external_id=external_id).values_list("pk")[0][0]

    @staticmethod
    def get_user_by_external_id(external_id):
        """
        Get the user id from external id
        :param external_id: User external id
        :return: The User instance
        """
        return User.get_user_by_id(User.get_user_id_by_external_id(external_id))

    @staticmethod
    @Cached()
    def get_user_items(user_id):
        """
        Get user items
        :param user_id: User id
        :return: A list of user items in inventory
        """
        return {
            entry.item.pk: {
                "acquisition": entry.acquisition_date,
                "dropped": entry.dropped_date
            }
            for entry in Inventory.objects.filter(user_id=user_id)
        }

    @property
    def all_items(self):
        """
        All items from this user. Key item id and value the inventory register
        """
        items = User.get_user_items(self.pk)
        return {
            item_id: Item.get_item_by_id(item_id)
            for item_id, dates in items.items()
        }

    @property
    def owned_items(self):
        """
        Get the owned items from cache. Key item id and value the inventory register
        """
        items = User.get_user_items(self.pk)
        return {
            item_id: Item.get_item_by_id(item_id)
            for item_id, dates in items.items() if dates["dropped"] is None
        }

    @staticmethod
    def load_to_cache():
        for user in User.objects.all():
            user.load_user()

    def load_user(self):
        """
        Load a single user to cache
        """
        cache = get_cache("default")
        cache.set("get_user_by_id_%s" % self.pk, self, None)
        cache.set("get_user_id_by_external_id_%s" % self.external_id, self.pk, None)
        User.get_user_items(self.pk)

    def delete_user(self):
        """
        Load a single user to cache
        """
        cache = get_cache("default")
        cache.delete("get_user_by_id_%s" % self.pk)
        cache.delete("get_user_id_by_external_id_%s" % self.external_id)
        cache.delete("get_user_items_%s" % self.pk)

    @functools.wraps(lock)
    def load_item(self, entry):
        """
        Load a single inventory entry
        """
        cache = get_cache("default")
        entries = cache.get("get_user_items_%s" % self.pk, {})
        entries[entry.item.pk] = {
            "acquisition": entry.acquisition_date,
            "dropped": entry.dropped_date
        }
        cache.set("get_user_items_%s" % self.pk, entries)

    @functools.wraps(lock)
    def delete_item(self, entry):
        """
        Load a single inventory entry
        """
        cache = get_cache("default")
        entries = cache.get("get_user_items_%s" % self.pk, {})
        del entries[entry.item.pk]
        cache.set("get_user_items_%s" % self.pk, entries)


@receiver(post_save, sender=User)
def add_user_to_cache(sender, instance, created, raw, using, update_fields, *args, **kwargs):
    """
    Add item to cache upon creation
    """
    instance.load_user()


@receiver(post_delete, sender=User)
def delete_user_to_cache(sender, instance, using, *args, **kwargs):
    """
    Add item to cache upon creation
    """
    instance.delete_user()


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
    instance.user.load_item(instance)


@receiver(post_delete, sender=Inventory)
def delete_inventory_to_cache(sender, instance, using, *args, **kwargs):
    """
    Add item to cache upon creation
    """
    instance.user.delete_item(instance)


class Matrix(models.Model):
    """
    Numpy Matrix in database
    """

    name = models.CharField(_("name"), max_length=255)
    model_id = models.SmallIntegerField(_("model id"), null=True, blank=True)
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


class UserMatrix:

    @staticmethod
    @Cached()
    def get_user_array(index):
        return Matrix.objects.filter(name="tensorcofi", model_id=0).order_by("-id")[0].numpy[index, :]

    def __getitem__(self, index):
        return self.get_user_array(index)

    @functools.wraps(lock)
    def __setitem__(self, index, value):
        get_cache("default").set("get_user_array_%s" % str(index), value, None)

    @functools.wraps(lock)
    def __delitem__(self, index):
        get_cache("default").delete("get_user_array_%s" % str(index))


class TensorCoFi(PyTensorCoFi):
    """
    A creator of TensorCoFi models
    """

    #cache = CacheManager("tensorcofi")
    #user_matrix = CacheManager("tcumatrix")
    user_matrix = UserMatrix()

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
        return np.dot(self.factors[0][self.data_map[self.get_user_column()][user]],
                      self.factors[1][self.data_map[self.get_item_column()][item]].transpose())

    def get_recommendation(self, user, **context):
        """
        Get the recommendation for this user
        """
        return self.get_not_mapped_recommendation(user.pk-1, **context)

    @staticmethod
    def load_to_cache():
        tensor = TensorCoFi.get_model_from_cache()
        return tensor

    @staticmethod
    @Cached()
    def get_model_from_cache(*args, **kwargs):
        tensor = TensorCoFi(n_users=User.objects.all().count(), n_items=Item.objects.all().count())
        try:
            users = Matrix.objects.filter(name="tensorcofi", model_id=0).order_by("-id")[0]
            items = Matrix.objects.filter(name="tensorcofi", model_id=1).order_by("-id")[0]
        except IndexError:
            raise NotCached("%s not in db" % tensor.get_name())

        for i, u in enumerate(users.numpy):
            tensor.user_matrix[i] = u
        tensor.item_matrix = items.numpy
        tensor.factors = [tensor.user_matrix, tensor.item_matrix]
        return tensor

    @staticmethod
    def get_model(*args, **kwargs):
        return TensorCoFi.get_model_from_cache(args, **kwargs).factors

    @staticmethod
    def train_from_db(*args, **kwargs):
        """
        Trains the model in to data base
        """
        tensor = TensorCoFi(n_users=User.objects.all().count(), n_items=Item.objects.all().count())
        data = np.array(sorted([(u-1, i-1, 1.) for u, i in Inventory.objects.all().values_list("user_id", "item_id")]))
        return tensor.train(data)

    def train(self, data):
        """
        Trains the model in to data base
        """
        super(TensorCoFi, self).train(data)
        users, items = super(TensorCoFi, self).get_model()
        users = Matrix(name="tensorcofi", model_id=0, numpy=users)
        users.save()
        items = Matrix(name="tensorcofi", model_id=1, numpy=items)
        items.save()
        return users, items

    @staticmethod
    def drop_cache():
        get_cache("default").delete("get_model_from_cache")


@receiver(post_save, sender=Inventory)
def remove_user_from_tensorcofi_on_save(sender, instance, created, raw, using, update_fields, *args, **kwargs):
    """
    Remove user from tensorCoFi
    """
    del TensorCoFi.user_matrix[instance.user.pk-1]


@receiver(post_delete, sender=Inventory)
def remove_user_from_tensorcofi_on_delete(sender, instance, using, *args, **kwargs):
    """
    Remove user from tensorCoFi
    """
    del TensorCoFi.user_matrix[instance.user.pk-1]


@receiver(post_delete, sender=User)
def remove_user_from_tensorcofi_on_delete_user(sender, instance, using, *args, **kwargs):
    """
    Remove user from tensorCoFi
    """
    del TensorCoFi.user_matrix[instance.pk-1]


class Popularity(TestFMPopularity):
    """
    Popularity connector for db and test.fm
    """

    #cache = CacheManager("popularity")

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
        self.popularity_recommendation = []
        for i in range(self.n_items):
            self.popularity_recommendation.append(self._counts.get(i+1, 0.0))

        self.popularity_recommendation = np.array(self.popularity_recommendation)

    @property
    def recommendation(self):
        return np.array(self.popularity_recommendation).astype(np.float32)

    @recommendation.setter
    def recommendation(self, value):
        self.popularity_recommendation = value.tolist()
        self._counts = {i+1: value[i] for i in range(self.n_items)}

    @staticmethod
    @Cached()
    def load_popularity():
        model = Popularity(n_items=Item.objects.all().count())
        pop = Matrix.objects.filter(name="popularity").order_by("-id")[0]
        model.recommendation = pop.numpy
        return model

    @staticmethod
    def load_to_cache():
        return Popularity.load_popularity()

    @staticmethod
    def get_model():
        return Popularity.load_popularity()

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
        Matrix.objects.create(name="popularity", numpy=popular_model.recommendation)
    train_from_db = train

    @staticmethod
    def drop_cache():
        get_cache("default").delete("load_popularity")