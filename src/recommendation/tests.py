# -*- coding: utf-8 -*-
"""
Created on 29 January 2014

Test the tensorCoFi against the testfm.

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
"""
__author__ = "joaonrb"

import sys
import numpy as np
from recommendation.models import TensorModel, JavaTensorCoFi, Inventory, Item, User
from pkg_resources import resource_filename
sys.path.append(resource_filename(__name__, "/../bin"))
import modelcrafter as mc


class TestModels(object):
    """
    Test package for recommendation test models
    """

    ITEM_FILE_NUM = 2559
    USER_FILE_NUM = 35

    @classmethod
    def setup_class(cls):
        """
        Setup the test package
        Upload some data to data base
        """
        mc.main("items", resource_filename(mc.__name__, "/data/app"))
        mc.main("users", resource_filename(mc.__name__, "/data/user"))

    def test_items_in_db(self):
        """
        Test if the number of items in the data base is correct
        """



class TestTensorCoFi(object):
    """
    Test Package for the tensor matrix creator and data base connector
    """

    @staticmethod
    def test_tensor_matrix():
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





