# -*- coding: utf-8 -*-
'''
Created on 29 January 2014

Test the tensorCoFi against the testfm.

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
'''
__author__ = 'joaonrb'



import numpy as np
from ffos.recommender.models import TensorModel


class TestTensorCoFi(object):
    """

    """

    def test_tensor_matrix(self):
        """
        Tests the tensor matrix against the test.fm matrix
        """
        # loads installation data to pandas.DataFrame

        users, items = TensorModel.train()
        db_u = TensorModel.objects.filter(dim=0).order_by("-pk")[0].numpy_matrix
        db_a = TensorModel.objects.filter(dim=1).order_by("-pk")[0].numpy_matrix
        #Compare matrix calculated like test.fm to the one from database
        assert np.array_equal(users, db_u)
        assert np.array_equal(items, db_a)





