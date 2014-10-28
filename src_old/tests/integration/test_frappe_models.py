#! -*- encoding: utf-8 -*-
"""
This test package is fully dedicated to models module in recommendation app.
"""
__author__ = "joaonrb"

import numpy as np
import pandas as pd
import testfm
from testfm.models.tensorcofi import PyTensorCoFi
from testfm.models.baseline_model import Popularity as TFMPopularity
from testfm.evaluation.evaluator import Evaluator
from django.core.cache import get_cache
from pkg_resources import resource_filename
from django.test import TestCase
from recommendation.models import Matrix, Item, User, Inventory, TensorCoFi, Popularity

ITEMS = [
    {"id": 1, "name": "facemagazine", "external_id": "10001"},
    {"id": 2, "name": "twister", "external_id": "10002"},
    {"id": 3, "name": "gfail", "external_id": "10003"},
    {"id": 4, "name": "appwhat", "external_id": "10004"},
    {"id": 5, "name": "pissedoffbirds", "external_id": "98766"},
]


USERS = [
    {"id": 1, "external_id": "joaonrb", "items": ["10001", "10003", "10004"]},
    {"id": 2, "external_id": "mumas", "items": ["10003", "10004", "98766"]},
    {"id": 3, "external_id": "alex", "items": ["10003"]},
    {"id": 4, "external_id": "rob", "items": ["10003", "10004"]},
    {"id": 5, "external_id": "gabriela", "items": ["10002", "98766"]},
    {"id": 6, "external_id": "ana", "items": []},
    {"id": 7, "external_id": "margarida", "items": ["10001", "98766"]},
]


class TestModels(TestCase):
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
        for i, app in enumerate(ITEMS, start=1):
            Item.objects.create(pk=(i*2), **app)
        for i, u in enumerate(USERS, start=1):
            user = User.objects.create(pk=(i*2), external_id=u["external_id"])
            for item in u["items"]:
                Inventory.objects.create(user=user, item=Item.get_item_by_external_id(item))

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        Item.objects.all().delete()
        User.objects.all().delete()
        Inventory.objects.all().delete()
        Matrix.objects.all().delete()
        get_cache("default").clear()
        get_cache("local").clear()

    def test_fit(self):
        """
        [recommendation.models.TensorCoFi] Test size of matrix after tensorCoFi fit
        """
        tf = TensorCoFi(n_users=len(self.df.user.unique()), n_items=len(self.df.item.unique()), n_factors=2)
        tf.fit(self.df)
        #item and user are row vectors
        #self.assertEqual(len(self.df.user.unique()), tf.factors[0].shape[0])
        self.assertEqual(len(self.df.item.unique()), tf.factors[1].shape[0])

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
            if len(user.owned_items) > 2:
                assert isinstance(t.get_recommendation(user), np.ndarray), "Recommendation is not a numpy array"
            else:
                try:
                    t.get_recommendation(user)
                except KeyError:
                    pass
                else:
                    assert False, "User with less than 3 items give a static recommendation"

    def test_tensor_score_against_testfm(self):
        """
        [recommendation.models.TensorCoFi] Test tensorcofi scores with test.fm benchmark
        """
        evaluator = Evaluator()
        tc = TensorCoFi(n_users=len(self.df.user.unique()), n_items=len(self.df.item.unique()), n_factors=2)
        ptc = PyTensorCoFi()
        training, testing = testfm.split.holdoutByRandom(self.df, 0.9)

        items = training.item.unique()
        tc.fit(training)
        ptc.fit(training)
        tc_score = evaluator.evaluate_model(tc, testing, all_items=items)[0]
        ptc_score = evaluator.evaluate_model(ptc, testing, all_items=items)[0]
        assert abs(tc_score-ptc_score) < .15, \
            "TensorCoFi score is not close enough to testfm benchmark (%.3f != %.3f)" % (tc_score, ptc_score)

    def test_popularity_score_against_testfm(self):
        """
        [recommendation.models.TensorCoFi] Test popularity scores with test.fm benchmark
        """
        evaluator = Evaluator()
        training, testing = testfm.split.holdoutByRandom(self.df, 0.9)
        items = training.item.unique()

        tc = Popularity(len(items))
        ptc = TFMPopularity()
        tc.fit(training)
        ptc.fit(training)
        tc_score = evaluator.evaluate_model(tc, testing, all_items=items)[0]
        ptc_score = evaluator.evaluate_model(ptc, testing, all_items=items)[0]
        assert abs(tc_score-ptc_score) < .1, \
            "Popularity score is not close enough to testfm benchmark (%.3f != %.3f)" % (tc_score, ptc_score)
