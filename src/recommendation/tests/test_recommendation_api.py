#! -*- encoding: utf-8 -*-
"""
This test package test the recommendation api
"""
__author__ = "joaonrb"

import json
import pandas as pd
import numpy as np
from pkg_resources import resource_filename
from django.test import TestCase
from django.test.client import Client, MULTIPART_CONTENT
from testfm.evaluation import Evaluator
from testfm.models.tensorcofi import PyTensorCoFi
import recommendation
from recommendation.management.commands import fill, modelcrafter
from recommendation.models import Item, User, Inventory, Matrix, TensorCoFi, Popularity


class TestRecommendation(TestCase):
    """
    Test suite for recommendation system

    Test:
        - Get recommendation
        - Test recommendation against test.fm results
    """

    @classmethod
    def setup_class(cls, *args, **kwargs):
        """
        Put elements in db
        """
        path = resource_filename(recommendation.__name__, "/")
        fill.main("items", path + "data/app")
        fill.main("users", path + "data/user")
        modelcrafter.main("train", "popularity")
        modelcrafter.main("train", "tensorcofi")
        # Load user and items
        Item.load_to_cache()
        User.load_to_cache()
        # Load main models
        Popularity.load_to_cache()
        TensorCoFi.load_to_cache()
        cls.client = Client()

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        # This for sqlite delete
        while Item.objects.all().count() != 0:
            Item.objects.all()[:100].delete()
        User.objects.all().delete()
        Matrix.objects.all().delete()

    def test_get_recommendation(self):
        """
        [recommendation.api.GetRecommendation] Get recommendation as json
        """
        response = self.client.get("/api/v2/recommend/5/")
        assert response.status_code == 200, "Request failed. Status code %d." % response.status_code
        rec = json.loads(response.content)
        assert rec["user"] in map(lambda x: x.external_id, User.user_by_external_id), "User don't exist in cache"
        assert len(rec["recommendations"]) == 5, "Size of recommendation not 5"

    def test_recommendation_with_testfm(self):
        """
        [recommendation.api.GetRecommendation] Test recommendation with testfm
        """
        """
        users, items = zip(*Inventory.objects.all().values_list("user_id", "item_id"))
        df = pd.DataFrame({"user": pd.Series(users, dtype=np.int32), "item": pd.Series(items, dtype=np.int32)})
        evaluator = Evaluator(use_multi_threading=False)
        #training, testing = testfm.split.holdoutByRandom(df, 0.2)
        tensor = TensorCoFi.get_model()
        tfm_tensor = PyTensorCoFi()
        tfm_tensor.fit(df)
        items = pd.Series((i+1 for i in range(len(Item.item_by_id))), dtype=np.int32)

        t = evaluator.evaluate_model(tensor, df, all_items=items, non_relevant_count=100),
        tfm = evaluator.evaluate_model(tfm_tensor, df, all_items=items, non_relevant_count=100)
        assert abs(t - tfm) < 0.10, "Difference between testfm implementation and frappe is to high."
        """
        data = np.array(zip(*map(lambda x: (x["user_id"]-1, x["item_id"]-1, 1.),
                                 Inventory.objects.all().values("user_id", "item_id"))), dtype=np.float32)
        users, items = zip(*Inventory.objects.all().values_list("user_id", "item_id"))
        df = pd.DataFrame({"user": pd.Series(users), "item": pd.Series(items)}, dtype=np.float32)
        evaluator = Evaluator(use_multi_threading=False)
        #training, testing = testfm.split.holdoutByRandom(df, 0.2)
        tensor = TensorCoFi.get_model_from_cache()
        tfm_tensor = PyTensorCoFi()
        tfm_tensor.data_map = tensor.data_map
        tfm_tensor.users_size = lambda: tensor.users_size()
        tfm_tensor.items_size = lambda: tensor.items_size()
        tfm_tensor.get_score = lambda user, item: \
            np.dot(tfm_tensor.factors[0][tfm_tensor.data_map[tfm_tensor.get_user_column()][user]],
                   tfm_tensor.factors[1][tfm_tensor.data_map[tfm_tensor.get_item_column()][item]].transpose())
        tfm_tensor.train(data.transpose())
        items = df.item.unique()
        t = evaluator.evaluate_model(tensor, df, all_items=items, non_relevant_count=100)
        tfm = evaluator.evaluate_model(tfm_tensor, df, all_items=items, non_relevant_count=100)
        assert abs(t[0] - tfm[0]) < 0.10, \
            "Difference between testfm implementation and frappe is to high (%f, %f)" % (t[0], tfm[0])


class TestUserItems(TestCase):
    """
    Test suite for recommendation system

    Test:
        - Get user item
        - Install user item
        - Drop user item
    """

    @classmethod
    def setup_class(cls, *args, **kwargs):
        """
        Put elements in db
        """
        path = resource_filename(recommendation.__name__, "/")
        fill.main("items", path + "data/app")
        fill.main("users", path + "data/user")
        modelcrafter.main("train", "popularity")
        modelcrafter.main("train", "tensorcofi")
        # Load user and items
        Item.load_to_cache()
        User.load_to_cache()
        # Load main models
        Popularity.load_to_cache()
        TensorCoFi.load_to_cache()
        cls.client = Client()

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        # This for sqlite delete
        while Item.objects.all().count() != 0:
            Item.objects.all()[:100].delete()
        User.objects.all().delete()
        Matrix.objects.all().delete()

    def test_recommendation_get_user_item(self):
        """
        [recommendation.api.GetUserItems] Test Get user items
        """
        response = \
            self.client.get("/api/v2/user-items/0047765d0b6165476b11297e58a341c357af9c35e12efd8c060dabe293ea338d/")
        assert response.status_code == 200, "Request failed. Status code %d." % response.status_code
        its = json.loads(response.content)
        assert its["user"] == "0047765d0b6165476b11297e58a341c357af9c35e12efd8c060dabe293ea338d", "User is not correct"
        assert its["items"][0]["external_id"] == 372826, "Owned item is not 372826"
        assert len(its["items"]) == 1, "Owned items should be 1"

    def test_recommendation_acquire_new_item(self):
        """
        [recommendation.api.GetUserItems] Test acquire new item
        """
        response = self.client.post(
            "/api/v2/user-items/00504e6196ab5fa37ae7450dad99d031a80c50ef4b762c15151a2e4e92c64e0b/",
            {"item_to_acquire": 457468}
        )
        user = User.user_by_external_id["00504e6196ab5fa37ae7450dad99d031a80c50ef4b762c15151a2e4e92c64e0b"]
        assert response.status_code == 200, "Request failed. Status code %d." % response.status_code
        assert len(user.owned_items) == 3, "Owned items should be 3(%d)" % len(user.owned_items)
        assert Item.item_by_external_id[457468].pk in user.owned_items, "New item not in owned items"

    def test_recommendation_remove_new_item(self):
        """
        [recommendation.api.GetUserItems] Test remove old item
        """
        response = self.client.delete(
            "/api/v2/user-items/006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173/",
            "item_to_remove=413346",
            content_type="application/x-www-form-urlencoded; charset=UTF-8"
        )
        assert response.status_code == 200, "Request failed. Status code %d. Message: %s" % \
                                            (response.status_code, json.loads(response.content).get("error", ""))
        assert len(User.user_by_external_id[
                       "006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173"].owned_items) == 0, \
            "Owned items should be 0"