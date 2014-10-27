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
import click
try:
    import cPickle as pickle
except ImportError:
    import pickle
from six import string_types
from django.db import models
from django.utils.translation import ugettext as _
from django.utils.six import with_metaclass
from django.core.cache import get_cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from testfm.models.tensorcofi import PyTensorCoFi
from testfm.models.baseline_model import Popularity as TestFMPopularity
from recommendation.decorators import Cached


class MappedField(with_metaclass(models.SubfieldBase, models.TextField)):
    """
    Mapped structure to be saved in database.
    """

    description = """Mapped structure."""
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """
        Convert the value from the database to python like object

        >>> # Dictionary with numpy array
        >>> # {1: np.np.array([1, 2, 3, 4], dtype=np.float32)}
        >>> string = "(dp1\nI1\ncnumpy.core.multiarray\n_reconstruct\np2\n(cnumpy\nndarray\np3\n(I0\ntS'b'\ntRp4\n(I1\n(I4\ntcnumpy\ndtype\np5\n(S'f4'\nI0\nI1\ntRp6\n(I3\nS'<'\nNNNI-1\nI-1\nI0\ntbI00\nS'\\x00\\x00\\x80?\\x00\\x00\\x00@\\x00\\x00@@\\x00\\x00\\x80@'\ntbs."
        >>> some_dict = MappedField().to_python(string)

        >>> print(some_dict)
        {1: array([ 1.,  2.,  3.,  4.], dtype=float32)}

        >>> type(some_dict)
        <type 'dict'>

        >>> len(some_dict[1].shape) == 1  # Has one dimension
        True

        >>> for i in some_dict[1]:
        ...     print(i)
        ...     print(type(i))
        1.0
        <type 'numpy.float32'>
        2.0
        <type 'numpy.float32'>
        3.0
        <type 'numpy.float32'>
        4.0
        <type 'numpy.float32'>

        :param value: String from database
        :return: A numpy matrix
        """
        if isinstance(value, string_types):
            return pickle.loads(value)
        return value

    def get_prep_value(self, value):
        """
        Prepare the value from python like object to database like value.

        >>> some_dict = {1: np.array([1, 2, 3, 4], dtype=np.float32)}
        >>> string = MappedField().get_prep_value(some_dict)
        >>> print(string)
        (dp1
        I1
        cnumpy.core.multiarray
        _reconstruct
        p2
        (cnumpy
        ndarray
        p3
        (I0
        tS'b'
        tRp4
        (I1
        (I4
        tcnumpy
        dtype
        p5
        (S'f4'
        I0
        I1
        tRp6
        (I3
        S'<'
        NNNI-1
        I-1
        I0
        tbI00
        S'\x00\x00\x80?\x00\x00\x00@\x00\x00@@\x00\x00\x80@'
        tbs.

        :param value: Matrix to keep in database
        :return: Base64 representation string encoded in utf-8
        """
        if isinstance(value, dict):
            return pickle.dumps(value)


class Item(models.Model):
    """
    Item to be used by recommending system
    """
    name = models.CharField(_("name"), max_length=255)
    external_id = models.CharField(_("external id"), max_length=255, unique=True)

    @staticmethod
    def get_item_by_id(item_id):
        """
        Return item by id.
        """
        return Item.get_item_by_external_id(Item.get_item_external_id_by_id(item_id))

    @staticmethod
    @Cached()
    def get_item_external_id_by_id(item_id):
        """
        Return item id from external_id.
        """
        return Item.objects.filter(pk=item_id).values_list("external_id")[0][0]

    @staticmethod
    @Cached()
    def get_item_by_external_id(external_id):
        """
        Return item from external id.
        """
        return Item.objects.get(external_id=external_id)

    def put_item_to_cache(self):
        """
        Loads an app to database.
        """
        Item.get_item_by_external_id.lock_this(
            Item.get_item_by_external_id.cache.set
        )(Item.get_item_by_external_id.key % self.external_id, self, Item.get_item_by_external_id.timeout)
        Item.get_item_external_id_by_id.lock_this(
            Item.get_item_external_id_by_id.cache.set
        )(Item.get_item_external_id_by_id.key % self.pk, self.external_id, Item.get_item_external_id_by_id.timeout)

    def del_item_from_cache(self):
        """
        delete an app to database
        """
        Item.get_item_by_external_id.lock_this(
            Item.get_item_by_external_id.cache.delete
        )(Item.get_item_by_external_id.key % self.external_id)
        Item.get_item_external_id_by_id.lock_this(
            Item.get_item_external_id_by_id.cache.delete
        )(Item.get_item_external_id_by_id.key % self.pk)

    class Meta:
        verbose_name = _("item")
        verbose_name_plural = _("items")

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.name)

    @staticmethod
    def load_to_cache():
        with click.progressbar(Item.objects.all(), label="Loading items to cache") as bar:
            for item in bar:
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
            entry.item_id: entry.is_dropped
            for entry in Inventory.objects.filter(user_id=user_id)
        }

    @property
    def all_items(self):
        """
        All items from this user. Key item id and value the inventory register
        """
        return {
            item_id: Item.get_item_by_id(item_id)
            for item_id, is_dropped in User.get_user_items(self.pk).items()
        }

    @property
    def owned_items(self):
        """
        Get the owned items from cache. Key item id and value the inventory register
        """
        return {
            item_id: Item.get_item_by_id(item_id)
            for item_id, is_dropped in User.get_user_items(self.pk).items() if not is_dropped
        }

    def has_more_than(self, n):
        """
        Check if user has more than n items owned
        """
        count = 0
        for is_dropped in User.get_user_items(self.pk).values():
            if not is_dropped:
                count += 1
                if count > n:
                    return True
        return False

    @staticmethod
    def load_to_cache():
        with click.progressbar(User.objects.all(), label="Loading users to cache") as bar:
            for user in bar:
                User.get_user_by_id.lock_this(
                    User.get_user_by_id.cache.set
                )(User.get_user_by_id.key % user.pk, user, User.get_user_by_id.timeout)
            User.get_user_id_by_external_id.lock_this(
                User.get_user_id_by_external_id.cache.set
            )(User.get_user_id_by_external_id.key % user.external_id, user.pk, User.get_user_id_by_external_id.timeout)
        lenght = Inventory.objects.all().count()
        with click.progressbar(range(0, lenght, 100000),
                               label="Loading owned items to cache") as bar:
            inventory = {}
            max_id = 0
            for i in bar:
                for max_id, user_id, item_id, is_dropped in Inventory.objects.filter(id__gt=max_id)\
                        .order_by("pk")[i:i+100000].values_list("pk", "user_id", "item_id", "is_dropped"):
                    try:
                        inventory[user_id][item_id] = is_dropped
                    except KeyError:
                        inventory[user_id] = {
                            item_id: is_dropped
                        }
            for ueid, items in inventory.items():
                User.get_user_items.lock_this(
                    User.get_user_items.cache.set
                )(User.get_user_items.key % ueid, items, User.get_user_items.timeout)

    def load_user(self):
        """
        Load a single user to cache
        """
        User.get_user_by_id.lock_this(
            User.get_user_by_id.cache.set
        )(User.get_user_by_id.key % self.pk, self, User.get_user_by_id.timeout)
        User.get_user_id_by_external_id.lock_this(
            User.get_user_id_by_external_id.cache.set
        )(User.get_user_id_by_external_id.key % self.external_id, self.pk, User.get_user_id_by_external_id.timeout)
        User.get_user_items(self.pk)

    def delete_user(self):
        """
        Load a single user to cache
        """
        User.get_user_by_id.lock_this(
            User.get_user_by_id.cache.delete
        )(User.get_user_by_id.key % self.external_id)
        User.get_user_id_by_external_id.lock_this(
            User.get_user_id_by_external_id.cache.delete
        )(User.get_user_id_by_external_id.key % self.external_id)
        User.get_user_items.lock_this(
            User.get_user_items.cache.delete
        )(User.get_user_items.key % self.external_id)

    def load_item(self, entry):
        """
        Load a single inventory entry
        """
        cache = User.get_user_items.cache
        entries = cache.get(User.get_user_items.key % self.pk, {})
        entries[entry.item_id] = entry.is_dropped
        cache.set(User.get_user_items.key % self.pk, entries)

    def delete_item(self, entry):
        """
        Load a single inventory entry
        """
        cache = User.get_user_items.cache
        entries = cache.get(User.get_user_items.key % self.pk, {})
        try:
            del entries[entry.item.pk]
        except KeyError:
            pass
        cache.set(User.get_user_items.key % self.pk, entries)


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
    #acquisition_date = models.DateTimeField(_("acquisition date"))
    #dropped_date = models.DateTimeField(_("dropped date"), null=True, blank=True)
    is_dropped = models.BooleanField(_("is dropped"), default=False)

    class Meta:
        verbose_name = _("owned item")
        verbose_name_plural = _("owned items")
        #unique_together = ("user", "item")

    def __str__(self):
        return _("%(state)s %(item)s item for user %(user)s") % {
            "state": _("dropped") if self.is_dropped else _("owned"), "item": self.item.name,
            "user": self.user.external_id}

    def __unicode__(self):
        return _("%(state)s %(item)s item for user %(user)s") % {
            "state": _("dropped") if self.is_dropped else _("owned"), "item": self.item.name,
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
        if not User.get_user_by_id(index+1).has_more_than(2):  # Index+1 = User ID
            raise KeyError("User %d static recommendation doesn't exist" % (index+1))
        return Matrix.objects.filter(name="tensorcofi", model_id=0).order_by("-id")[0].numpy[index, :]

    def __getitem__(self, index):
        return self.get_user_array(index)

    def __setitem__(self, index, value):
        try:
            if User.get_user_by_id(index+1).has_more_than(2):  # Index+1 = User ID
                dec = UserMatrix.get_user_array
                dec.lock_this(
                    dec.cache.set
                )(dec.key % index, value, dec.timeout)
        except User.DoesNotExist:
            pass

    def __delitem__(self, index):
        dec = UserMatrix.get_user_array
        dec.lock_this(
            dec.cache.delete
        )(dec.key % index)


class FactorsContainer:

    def __init__(self, model):
        self.__model = model

    def __getitem__(self, index):
        return [self.__model.user_matrix, self.__model.get_item_matrix()][index]


class TensorCoFi(PyTensorCoFi):
    """
    A creator of TensorCoFi models
    """

    user_matrix = UserMatrix()

    def __init__(self, n_users=None, n_items=None, **kwargs):
        """
        """
        if not isinstance(n_items, int) or not isinstance(n_users, int):
            raise AttributeError("Parameter n_items and n_users must be integers")
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
        factors = [Matrix.objects.filter(name="tensorcofi", model_id=0).order_by("-id")[0].numpy,
                   Matrix.objects.filter(name="tensorcofi", model_id=1).order_by("-id")[0].numpy]
        return np.dot(factors[0][self.data_map[self.get_user_column()][user]],
                      factors[1][self.data_map[self.get_item_column()][item]].transpose())

    def get_recommendation(self, user, **context):
        """
        Get the recommendation for this user
        """
        return self.get_not_mapped_recommendation(user.pk-1, **context)

    @staticmethod
    def load_to_cache():
        try:
            users = Matrix.objects.filter(name="tensorcofi", model_id=0).order_by("-id")[0]
        except IndexError:
            raise NotCached("TensorCoFi not in db")

        with click.progressbar(enumerate(users.numpy),
                               length=users.numpy.shape[0],
                               label="Loading TensorCoFi users to cache") as bar:
            for i, u in bar:
                TensorCoFi.user_matrix[i] = u
        TensorCoFi.get_item_matrix()

    @staticmethod
    @Cached(cache="local")
    def get_item_matrix():
        try:
            items = Matrix.objects.filter(name="tensorcofi", model_id=1).order_by("-id")[0]
        except IndexError:
            raise NotCached("tensocofi model not in db")
        return items.numpy

    @staticmethod
    @Cached(cache="local")
    def get_model_from_cache(*args, **kwargs):
        tensor = TensorCoFi(n_users=User.objects.aggregate(max=models.Max("pk"))["max"],
                            n_items=Item.objects.aggregate(max=models.Max("pk"))["max"])
        tensor.factors = FactorsContainer(tensor)
        return tensor


    @staticmethod
    def get_model(*args, **kwargs):
        return TensorCoFi.get_model_from_cache(args, **kwargs).factors

    @staticmethod
    def train_from_db(*args, **kwargs):
        """
        Trains the model in to data base
        """
        tensor = TensorCoFi(n_users=User.objects.aggregate(max=models.Max("pk"))["max"],
                            n_items=Item.objects.aggregate(max=models.Max("pk"))["max"])
        data = np.array(sorted([(u-1, i-1, 1) for u, i in Inventory.objects.all().values_list("user_id", "item_id")]))
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
        TensorCoFi.get_model_from_cache.cache.delete("get_model_from_cache")


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

    def __init__(self, n_items=None, *args, **kwargs):

        if not isinstance(n_items, int):
            raise AttributeError("Parameter n_items must be integer")
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
    @Cached(cache="local")
    def load_popularity():
        model = Popularity(n_items=Item.objects.aggregate(max=models.Max("pk"))["max"])
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
        popular_model = Popularity(n_items=Item.objects.aggregate(max=models.Max("pk"))["max"])
        users, items = zip(*Inventory.objects.all().values_list("user_id", "item_id"))
        data = pd.DataFrame({"item": items, "user": users})
        popular_model.fit(data)
        Matrix.objects.create(name="popularity", numpy=popular_model.recommendation)
    train_from_db = train

    @staticmethod
    def drop_cache():
        get_cache("default").delete("load_popularity")
