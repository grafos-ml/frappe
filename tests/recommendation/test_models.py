#! -*- encoding: utf-8 -*-
"""
This test package is fully dedicated to models module in recommendation app.
"""
__author__ = "joaonrb"

import sys
import numpy as np
from django.utils import timezone as dt
from django.test import TestCase
from recommendation.models import CacheManager, Matrix, Item, User, Inventory
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
        result.append((n/last)%i)
        last *= i
    return result


class TestNPArrayField(TestCase):
    """
    Test suit for NPArray field

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
    Test suit for cache manager

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
            self.cache[key] = value
        values = list(self.data.values())
        for value in self.cache:
            assert value in values, "Item in cache iterator is not in test data (%s not in %s)" % (value, values)
        for _, value in self.data.items():
            assert value in self.cache, "Test item not in cache (%s not in %s)" % (value, list(self.cache))

    def test_cache_size(self):
        """
        [recommendation.models.CacheManager] Test the size of cache
        """
        # Adding values
        for key, value in self.data.items():
            self.cache[key] = value
        # Two times to check for replications
        for key, value in self.data.items():
            self.cache[key] = value
        assert len(self.cache) == len(self.data), "Size of test data and cache are not the same (%d != %d)" % \
                                                  (len(self.cache), len(self.data))


ITEMS = [
    {"id": 1, "name": "facemagazine", "external_id": "10001"},
    {"id": 2, "name": "twister", "external_id": "10002"},
    {"id": 3, "name": "gfail", "external_id": "10003"},
    {"id": 4, "name": "appwhat", "external_id": "10004"},
    {"id": 5, "name": "pissedoffbirds", "external_id": "98766"},
]


USERS = [
    {"id": 1, "external_id": "joaonrb", "items": [1, 3, 4]},
    {"id": 2, "external_id": "mumas", "items": [3, 4, 5]},
    {"id": 3, "external_id": "alex", "items": [3]},
    {"id": 4, "external_id": "rob", "items": [3, 4]},
    {"id": 5, "external_id": "gabriela", "items": [2, 5]},
    {"id": 6, "external_id": "ana", "items": []},
    {"id": 7, "external_id": "margarida", "items": [1, 5]},
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

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        Item.objects.all().delete()

    def test_get_item_by_id(self):
        """
        [recommendation.models.Item] Test queries by id made by getting items and check integrity of that items
        """
        with self.assertNumQueries(0):
            for app in ITEMS:
                item = Item.item_by_id[app["id"]]
                assert isinstance(item, Item), "Cached item is not instance of Item."
                assert item.name == app["name"], "Name of the app is not correct"
                assert item.external_id == app["external_id"], "External id is not correct"

    def test_get_item_by_external_id(self):
        """
        [recommendation.models.Item] Test queries by external id made by getting items and check integrity of that items
        """
        with self.assertNumQueries(0):
            for app in ITEMS:
                item = Item.item_by_external_id[app["external_id"]]
                assert isinstance(item, Item), "Cached item is not instance of Item."
                assert item.name == app["name"], "Name of the app is not correct"
                assert item.pk == app["id"], "Id is not correct"


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
            user = User.objects.create(id=u["id"], external_id=u["external_id"])
            for i in u["items"]:
                Inventory.objects.create(user=user, item=Item.item_by_id[i], acquisition_date=dt.now())

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        Item.objects.all().delete()
        User.objects.all().delete()

    def test_get_user_by_id(self):
        """
        [recommendation.models.User] Test queries by id made by getting user and check integrity of that user
        """
        with self.assertNumQueries(0):
            for u in USERS:
                user = User.user_by_id[u["id"]]
                assert isinstance(user, User), "Cached user is not instance of User."
                assert user.external_id == u["external_id"], "External id is not correct"

    def test_get_item_by_external_id(self):
        """
        [recommendation.models.User] Test queries by external id made by getting user and check integrity of that user
        """
        with self.assertNumQueries(0):
            for u in USERS:
                user = User.user_by_external_id[u["external_id"]]
                assert isinstance(user, User), "Cached user is not instance of User."
                assert user.pk == u["id"], "Id is not correct"

    def test_owned_items(self):
        """

        :return:
        """