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
from django.core.cache import get_cache
from django.core.management import call_command
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
        fill.FillTool({"items": True, "--mozilla": True, "prod": True}).load()
        fill.FillTool({"users": True, "--mozilla": True, "<path>": path+"data/user"}).load()
        #call_command("fill", "items --mozilla prod")
        #call_command("fill", "users", "--mozilla", path+"data/user")
        call_command("modelcrafter", "train", "popularity")
        call_command("modelcrafter", "train", "tensorcofi")
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
            Item.objects.filter(pk__in=Item.objects.all()[:100]).delete()
        User.objects.all().delete()
        Matrix.objects.all().delete()
        Popularity.drop_cache()
        TensorCoFi.drop_cache()
        get_cache("default").clear()
        get_cache("local").clear()

    def test_get_recommendation(self):
        """
        [recommendation.api.GetRecommendation] Get recommendation as json
        """
        response = \
            self.client.get("/api/v2/recommend/5/0047765d0b6165476b11297e58a341c357af9c35e12efd8c060dabe293ea338d/")
        assert response.status_code == 200, "Request failed. Status code %d." % response.status_code
        rec = json.loads(response.content)
        assert rec["user"] in map(lambda x: x.external_id, User.objects.all()), "User don't exist in cache"
        assert len(rec["recommendations"]) == 5, "Size of recommendation not 5"

    def test_recommendation_with_testfm(self):
        """
        [recommendation.api.GetRecommendation] Test recommendation with testfm
        """
        data = np.array(zip(*map(lambda x: (x["user_id"]-1, x["item_id"]-1, 1.),
                                 Inventory.objects.all().values("user_id", "item_id"))), dtype=np.float32)
        users, items = zip(*Inventory.objects.all().values_list("user_id", "item_id"))
        df = pd.DataFrame({"user": pd.Series(users), "item": pd.Series(items)}, dtype=np.float32)
        evaluator = Evaluator(use_multi_threading=False)
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