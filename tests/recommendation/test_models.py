#! -*- encoding: utf-8 -*-
"""
This test package is fully dedicated to models module in recommendation app.
"""
__author__ = "joaonrb"

import sys
import numpy as np
#from nose.tools import
from recommendation.models import CacheManager, Matrix
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


class TestNPArrayField(object):
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


class TestCacheManager(object):
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