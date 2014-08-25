#! -*- encoding: utf-8 -*-
"""
This test package test the core methods and controller.
"""
__author__ = "joaonrb"

import unittest as ut
from django.test import TestCase
from django.utils import timezone as dt
from recommendation.models import Item, User, Inventory, Matrix, TensorCoFi, Popularity
from recommendation.core import IController, TensorCoFiController, get_controller, RECOMMENDATION_SETTINGS, \
    ControllerNotDefined


class TestGetController(TestCase):
    """
    Test case for accessing different controllers
    """

    @ut.skipIf("default" not in RECOMMENDATION_SETTINGS, "Default recommendation is not defined")
    def test_get_default(self):
        """
        [recommendation.core.Util] Test get default recommendation controller
        """
        try:
            rec = get_controller()
        except ControllerNotDefined:
            assert False, "Default controller is throwing ControllerNotDefined exception"
        assert isinstance(rec, IController), "Recommendation in result is not IController instance"

    @ut.skipIf("not default" in RECOMMENDATION_SETTINGS, "Not default recommendation is insanely defined")
    def test_get_not_default(self):
        """
        [recommendation.core.Util] Test get "not default" recommendation controller
        """
        try:
            get_controller("not default")
            assert False, "Not default controller is not throwing ControllerNotDefined exception"
        except ControllerNotDefined:
            pass


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


class TestTensorCoFiController(TestCase):
    """
    Test the controller for a recommendation.
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
        TensorCoFi.train_from_db()
        Popularity.train_from_db()
        TensorCoFi.load_to_cache()
        Popularity.load_to_cache()

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        Item.objects.all().delete()
        User.objects.all().delete()
        Matrix.objects.all().delete()

    @ut.skipIf("default" not in RECOMMENDATION_SETTINGS, "Default recommendation is not defined")
    def test_check_std_recommendation(self):
        """
        [recommendation.core.TensorCoFiController] Test get default recommendation
        """
        rec_controller = get_controller()
        for u in USERS:
            recommendation = rec_controller.get_recommendation(User.user_by_id[u["id"]], n=5)
            assert len(recommendation) == 5, "Size of recommendation is not wright"

    @ut.skipIf("default" not in RECOMMENDATION_SETTINGS, "Default recommendation is not defined")
    def test_check_alternative_recommendation(self):
        """
        [recommendation.core.TensorCoFiController] Test get alternative recommendation
        """
        rec_controller = get_controller()
        pop_result = \
            [aid+1 for aid, _ in sorted(enumerate(Popularity.get_model().recommendation),
                                        key=lambda x: x[1], reverse=True)]
        for i in range(7):
            user = User(external_id=str(i+len(USERS)))
            recommendation = rec_controller.get_recommendation(user, n=5)
            assert len(recommendation) == 5, "Size of recommendation is not wright"
            assert recommendation == pop_result, "Recommendation is not popularity"