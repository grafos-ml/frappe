#! -*- encoding: utf-8 -*-
"""
This test package is fully dedicated to models module in recommendation app.
"""
__author__ = "joaonrb"

import sys
import numpy as np
import pandas as pd
import testfm
import time
from pkg_resources import resource_filename
from django.utils import timezone as dt
from django.test import TestCase
from recommendation.models import IterableCacheManager, CacheManager, Matrix, Item, User, Inventory, TensorCoFi
if sys.version_info >= (3, 0):
    from functools import reduce


def get_coordinates(shape, n):
    """
    Get the coordinates bases on n
    :param shape: The shape of the matrix
    :param n: number of the element
    :return: a tuple of elements
    """
    last = 1
    result = []
    for i in shape:
        result.append((n/last) % i)
        last *= i
    return result


class TestNPArrayField(TestCase):
    """
    Test suite for NPArray field

    Must test:
        - Integrity of array on enter
        - Integrity of array on exit
    """

    array_samples = None
    MAX_ELEMENTS = 100

    @classmethod
    def setup_class(cls, *args, **kwargs):
        """
        Setup the sample arrays
        """
        if cls.array_samples is None:
            cls.array_samples = \
                [np.random.random(tuple(cls.MAX_ELEMENTS for _ in range(dim+1))).astype(np.float32) for dim in range(3)]

    def test_input_array_field(self):
        """
        [recommendation.models.NPArrayField] Test input numpy array for the field
        """
        for i in range(3):
            dim = i+1
            assert len(self.array_samples[i].shape) == dim, "The dimension of the input array %d is %d." % \
                                                            (dim, len(self.array_samples[i].shape))
            for j in range(dim):
                assert self.array_samples[i].shape[j] == self.MAX_ELEMENTS, \
                    "Array %d don't have %d elements at dimension %d (%d)." % (dim, self.MAX_ELEMENTS, j+1,
                                                                               self.array_samples[i].shape[j])

    def test_output_array_field(self):
        """
        [recommendation.models.NPArrayField] Test output numpy array for the field
        """
        for i in range(3):
            dim = i+1
            Matrix.objects.create(name=str(i), numpy=self.array_samples[i])
            db_array = Matrix.objects.get(name=str(i))
            assert len(db_array.numpy.shape) == dim, "The dimension of the output array %d is %d." % \
                                                     (dim, len(db_array.numpy.shape))
            for j in range(dim):
                assert db_array.numpy.shape[j] == self.MAX_ELEMENTS, \
                    "Array %d don't have %d elements at dimension %d (%d)." % (dim, self.MAX_ELEMENTS, j+1,
                                                                               db_array.numpy.shape[j])
            for elem_i in range(reduce(lambda x, y: x*y, db_array.numpy.shape)):
                coor = tuple(get_coordinates(db_array.numpy.shape, elem_i))
                assert db_array.numpy[coor] == self.array_samples[i][coor], \
                    u"Element at coordinates %s failed (%f != %f)" % (coor, db_array.numpy[coor],
                                                                      self.array_samples[i][coor])


class TestCacheManager(TestCase):
    """
    Test suite for cache manager

    Must test:
        - Put data
        - Get data
        - Iterate elements in manager
        - Check size in cache
    """

    @classmethod
    def setup_class(cls, *args, **kwargs):
        """
        Setup cache data
        """
        cls.data = {
            "k1": 1,
            "k2": "ldlçm",
            "k3": ["a", "b", "c"],
            "k4": {"this": "is", "just": "an", "example": "."}
        }
        cls.cache = CacheManager("test_suite")
        cls.icache = IterableCacheManager("test_suit_i")

    def test_input_in_cache(self):
        """
        [recommendation.models.CacheManager] Test input cache
        """
        for key, value in self.data.items():
            try:
                self.cache[key] = value
            except Exception as e:
                assert False, "Cached failed the input with error %s when entering a %s with key %s" % \
                              (str(e), str(type(value)), key)

    def test_output_in_cache(self):
        """
        [recommendation.models.CacheManager] Test output cache
        """
        for key, value in self.data.items():
            self.cache[key] = value
            assert self.cache[key] == value, "Cached output for key %s is not the same as value (%s != %s)" % \
                                             (key, self.cache[key], value)

    def test_iterate_in_cache(self):
        """
        [recommendation.models.CacheManager] Test iterate elements in cache
        """
        # Adding values
        for key, value in self.data.items():
            self.icache[key] = value
        values = list(self.data.values())
        for value in self.icache:
            assert value in values, "Item in cache iterator is not in test data (%s not in %s)" % (value, values)
        for _, value in self.data.items():
            assert value in self.icache, "Test item not in cache (%s not in %s)" % (value, list(self.icache))

    def test_cache_size(self):
        """
        [recommendation.models.CacheManager] Test the size of cache
        """
        # Adding values
        for key, value in self.data.items():
            self.icache[key] = value
        # Two times to check for replications
        for key, value in self.data.items():
            self.icache[key] = value
        assert len(self.icache) == len(self.data), "Size of test data and cache are not the same (%d != %d)" % \
                                                   (len(self.icache), len(self.data))


ITEMS = [
    {"name": "facemagazine", "external_id": "10001"},
    {"name": "twister", "external_id": "10002"},
    {"name": "gfail", "external_id": "10003"},
    {"name": "appwhat", "external_id": "10004"},
    {"name": "pissedoffbirds", "external_id": "98766"},
    ]


USERS = [
    {"external_id": "joaonrb", "items": ["10001", "10003", "10004"]},
    {"external_id": "mumas", "items": ["10003", "10004", "98766"]},
    {"external_id": "alex", "items": ["10003"]},
    {"external_id": "rob", "items": ["10003", "10004"]},
    {"external_id": "gabriela", "items": ["10002", "98766"]},
    {"external_id": "ana", "items": []},
    {"external_id": "margarida", "items": ["10001", "98766"]},
]


class TestItems(TestCase):
    """
    Test the item models

    ust test:
        - Number of queries when get item by id
        - Number of queries when get item by external id
    """

    @classmethod
    def setup_class(cls, *args, **kwargs):
        """
        Put elements in db
        """
        for app in ITEMS:
            Item.objects.create(**app)
        time.sleep(0.5)

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        Item.objects.all().delete()

    def test_get_item_by_external_id(self):
        """
        [recommendation.models.Item] Test queries by external id made by getting items and check integrity of that items
        """
        with self.assertNumQueries(0):
            for app in ITEMS:
                item = Item.get_item_by_external_id(app["external_id"])
                assert isinstance(item, Item), "Cached item is not instance of Item."
                assert item.name == app["name"], "Name of the app is not correct"


class TestUser(TestCase):
    """
    Test the user models

    ust test:
        - Number of queries when get item by id
        - Number of queries when get item by external id
        - Number of items
        - Number of owned items
    """

    @classmethod
    def setup_class(cls, *args, **kwargs):
        """
        Put elements in db
        """
        for app in ITEMS:
            Item.objects.create(**app)
        for u in USERS:
            user = User.objects.create(external_id=u["external_id"])
            for i in u["items"]:
                Inventory.objects.create(user=user, item=Item.get_item_by_external_id(i), acquisition_date=dt.now())

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        Item.objects.all().delete()
        User.objects.all().delete()
        Inventory.objects.all().delete()

    def test_get_item_by_external_id(self):
        """
        [recommendation.models.User] Test queries by external id made by getting user and check integrity of that user
        """
        with self.assertNumQueries(0):
            for u in USERS:
                user = User.get_user_by_external_id(u["external_id"])
                assert isinstance(user, User), "Cached user is not instance of User."

    def test_user_items(self):
        """
        [recommendation.models.User] Test user items
        """
        for u in USERS:
            user = User.get_user_by_external_id(u["external_id"])
            for i in u["items"]:
                assert Item.get_item_by_external_id(i).pk in user.all_items, \
                    "Item %s is not in user %s" % (i, user.external_id)

    def test_owned_items(self):
        """
        [recommendation.models.User] Test owned items
        """
        for u in USERS:
            user = User.get_user_by_external_id(u["external_id"])
            for i in u["items"]:
                ivent = Inventory.objects.get(item=user.all_items[Item.get_item_by_external_id(i).pk], user=user)
                ivent.dropped_date = dt.now()
                ivent.save()
                #user.load_item(ivent)
                time.sleep(.2)
                assert Item.get_item_by_external_id(i).pk not in user.owned_items, \
                    "Item %s is in user %s owned items" % (i, user.external_id)
                ivent = Inventory.objects.get(item=user.all_items[Item.get_item_by_external_id(i).pk], user=user)
                ivent.dropped_date = None
                ivent.save()


class TestTensorCoFi(TestCase):
    """
    Test suite for the tensorCoFi implementation for this recommendation
    """

    @classmethod
    def setup_class(cls, *args, **kwargs):
        """
        Put elements in db
        """
        cls.df = pd.read_csv(resource_filename(testfm.__name__, "data/movielenshead.dat"), sep="::", header=None,
                             names=["user", "item", "rating", "date", "title"])
        cls.df = cls.df.head(n=100)
        for i, app in enumerate(ITEMS, start=1):
            Item.objects.create(pk=(i*2), **app)
        for i, u in enumerate(USERS, start=1):
            user = User.objects.create(pk=(i*2), external_id=u["external_id"])
            for item in u["items"]:
                Inventory.objects.create(user=user, item=Item.get_item_by_external_id(item), acquisition_date=dt.now())

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        Item.objects.all().delete()
        User.objects.all().delete()
        Inventory.objects.all().delete()

    def test_fit(self):
        """
        [recommendation.models.TensorCoFi] Test size of matrix after tensorCoFi fit
        """
        tf = TensorCoFi(n_users=len(self.df.user.unique()), n_items=len(self.df.item.unique()), n_factors=2)
        tf.fit(self.df)
        #item and user are row vectors
        self.assertEqual(len(self.df.user.unique()), tf.factors[0].shape[0])
        self.assertEqual(len(self.df.item.unique()), tf.factors[1].shape[0])

    def test_score(self):
        """
        [recommendation.models.TensorCoFi] Test score in matrix
        """
        tf = TensorCoFi(n_users=len(self.df.user.unique()), n_items=len(self.df.item.unique()), n_factors=2)
        inp = [{"user": 10, "item": 100},
               {"user": 10, "item": 110},
               {"user": 12, "item": 120}]
        inp = pd.DataFrame(inp)
        tf.fit(inp)
        uid = tf.data_map[tf.get_user_column()][10]
        iid = tf.data_map[tf.get_item_column()][100]
        tf.factors[0][uid, 0] = 0
        tf.factors[0][uid, 1] = 1
        tf.factors[1][iid, 0] = 1
        tf.factors[1][iid, 1] = 5
        self.assertEqual(0*1+1*5, tf.get_score(10, 100))

    def test_training(self):
        """
        [recommendation.models.TensorCoFi] Test train from database
        """
        try:
            TensorCoFi.train_from_db()
        except Exception:
            assert False, "Training is not working for jumping ids"
        TensorCoFi.load_to_cache()
        t = TensorCoFi.get_model_from_cache()
        for user in User.objects.all():
            assert isinstance(t.get_recommendation(user), np.ndarray), "Recommendation is not a numpy array"
