# -*- coding: utf-8 -*-
"""
Created on 29 January 2014

Test the tensorCoFi against the testfm.

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
"""
__author__ = "joaonrb"

import sys
import numpy as np
from recommendation.models import TensorModel, Inventory, Item, User
from pkg_resources import resource_filename
sys.path.append(resource_filename(__name__, "/../bin"))
import fill


class TestModels(object):
    """
    Test package for recommendation test models
    """

    ITEMS_IN_DB = 2559
    USERS_IN_DB = 35
    ITEMS_IN_INVENTORY = 84

    @classmethod
    def setup_class(cls):
        """
        Setup the test package
        Upload some data to data base
        """
        fill.main("items", resource_filename(fill.__name__, "/data/app/"))
        fill.main("users", resource_filename(fill.__name__, "/data/user/"))

    def test_items_in_db(self):
        """
        Test if the number of items in the data base is correct
        """
        items_in_database = Item.objects.all().count()
        assert items_in_database == self.ITEMS_IN_DB, \
            "Number of items in data base(%s) are not correct(%s)" % (items_in_database, self.ITEMS_IN_DB)

    def test_users_in_db(self):
        """
        Test if the number of users in the data base is correct
        """
        users_in_database = User.objects.all().count()
        assert users_in_database == self.USERS_IN_DB, \
            "Number of users in data base(%s) are not correct(%s)" % (users_in_database, self.USERS_IN_DB)

    def test_items_in_inventory(self):
        """
        Test if the number of items in inventory is correct
        """
        owned_items_in_database = Inventory.objects.all().count()
        assert owned_items_in_database == self.ITEMS_IN_INVENTORY, \
            "Number of items in data inventory(%s) are not correct(%s)" % (owned_items_in_database,
                                                                           self.ITEMS_IN_INVENTORY)


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
        assert np.array_equal(users.numpy_matrix, db_u), "User matrix is not the same as in Java version"
        assert np.array_equal(items.numpy_matrix, db_a), "Item matrix is not the same as in Java version"





