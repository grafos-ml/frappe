#! -*- encoding: utf-8 -*-
"""
This test package is fully dedicated to models module in recommendation app.
"""
__author__ = "joaonrb"

import sys
import numpy as np
from recommendation.models import Matrix
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
        [recommendation.models] Test input numpy array for the field
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
        [recommendation.models] Test output numpy array for the field
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
                    "Element at coordinates %s failed (%f\u2260%f)" % (coor, db_array.numpy[coor],
                                                                       self.array_samples[i][coor])