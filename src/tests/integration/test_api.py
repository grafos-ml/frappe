#! -*- coding: utf-8 -*-
"""
frappe - tests.integration
joaonrb, 01 December 2014

Documentation TODO
"""

from __future__ import division, absolute_import, print_function
import json
import pandas as pd
import numpy as np
from time import sleep
from pkg_resources import resource_filename
from django.test import TestCase
from django.test.client import Client
from django.core.cache import get_cache
from testfm.evaluation import Evaluator
from testfm.models.tensorcofi import PyTensorCoFi
import frappe
from frappe.management.commands import fill, module
from frappe.models import Item, User, Inventory
from frappe.contrib.region.models import Region, UserRegion, ItemRegion
from frappe.contrib.diversity.models import ItemGenre, Genre

__author__ = "joaonrb"


class TestFrappeAPI(TestCase):
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
        path = resource_filename(frappe.__name__, "/")
        fill.FillTool({"items": True, "--mozilla": True, "prod": True}).load()
        fill.FillTool({"users": True, "--mozilla": True, "<path>": path+"data/user"}).load()
        module.FrappeCommand({"init": True, "--module": path+"../../frappe_settings_example.json", "<module>": "test"})
        module.FrappeCommand({"train": True, "<module>": "test"})
        module.FrappeCommand({"reloadslots": True})

        cls.client = Client()

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        ItemGenre.objects.all().delete()
        Genre.objects.all().delete()
        ItemRegion.objects.all().delete()
        UserRegion.objects.all().delete()
        Region.objects.all().delete()
        Inventory.objects.all().delete()
        User.objects.all().delete()
        Item.objects.all().delete()
        get_cache("default").clear()
        get_cache("owned_items").clear()
        get_cache("module").clear()

    def test_recommendation_get_user_item(self):
        """
        [recommendation.api.GetUserItems] Test Get user items
        """
        response = \
            self.client.get("/api/v2/user/00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961/"
                            "?page_size=1000")
        assert response.status_code == 200, "Request failed. Status code %d. %s" % (response.status_code,
                                                                                    response.content)
        its = json.loads(response.content)
        assert its["user"] == "00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961", "User is not correct"
        assert len(its["items"]) == 23, "Owned items should be 1"
        items = ["458731", "427484", "443388", "404175", "386137", "444510", "455256", "451558", "459110", "459621",
                 "404517", "448292", "442754", "462122", "463886", "404161", "438392", "464181", "460697", "458348",
                 "457808", "423716", "452888"]
        for item in items:
            assert item in its["items"], "Item %s not in request" % item

    def test_recommendation_acquire_new_item(self):
        """
        [recommendation.api.GetUserItems] Test acquire new item
        """
        response = self.client.post(
            "/api/v2/user/00504e6196ab5fa37ae7450dad99d031a80c50ef4b762c15151a2e4e92c64e0b/",
            {"item": "504343"},
            content_type="application/json"
        )
        sleep(0.8)
        user = User.get_user("00504e6196ab5fa37ae7450dad99d031a80c50ef4b762c15151a2e4e92c64e0b")
        assert response.status_code == 200, "Request failed. Status code %d." % response.status_code
        assert len(user.owned_items) == 3, "Owned items should be 3(%d)" % len(user.owned_items)
        assert "504343" in user.owned_items, "New item not in owned items"

    def test_recommendation_remove_new_item(self):
        """
        [recommendation.api.GetUserItems] Test remove old item
        """
        response = self.client.delete(
            "/api/v2/user/006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173/",
            json.dumps({"item": "413346"}),
            content_type="application/json"
        )
        sleep(0.8)
        assert response.status_code == 200, "Request failed. Status code %d. Message: %s" % \
                                            (response.status_code, json.loads(response.content).get("error", ""))
        assert len(User.get_user("006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173").owned_items) == 0,\
            "Owned items should be 0"


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
        path = resource_filename(frappe.__name__, "/")
        fill.FillTool({"items": True, "--mozilla": True, "prod": True}).load()
        fill.FillTool({"users": True, "--mozilla": True, "<path>": path+"data/user"}).load()
        module.FrappeCommand({"init": True, "--module": path+"../../frappe_settings_example.json", "<module>": "test"})
        module.FrappeCommand({"train": True, "<module>": "test"})
        module.FrappeCommand({"reloadslots": True})
        cls.client = Client()

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        ItemGenre.objects.all().delete()
        Genre.objects.all().delete()
        ItemRegion.objects.all().delete()
        UserRegion.objects.all().delete()
        Region.objects.all().delete()
        Inventory.objects.all().delete()
        User.objects.all().delete()
        Item.objects.all().delete()
        get_cache("default").clear()
        get_cache("owned_items").clear()
        get_cache("module").clear()

    def test_get_recommendation_more_than_3(self):
        """
        [recommendation.api.GetRecommendation] Get recommendation as json for a user with more than 3 apps
        """
        response = \
            self.client.get("/api/v2/recommend/5/00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961/")
        assert response.status_code == 200, "Request failed. Status code %d." % response.status_code
        rec = json.loads(response.content)
        assert rec["user"] in map(lambda x: x.external_id, User.objects.all()), "User don't exist in cache"
        assert len(rec["recommendations"]) == 5, "Size of recommendation not 5"

    def test_get_recommendation_less_than_3(self):
        """
        [recommendation.api.GetRecommendation] Get recommendation as json for a user with less than 3 apps
        """
        response = \
            self.client.get("/api/v2/recommend/5/0047765d0b6165476b11297e58a341c357af9c35e12efd8c060dabe293ea338d/")
        assert response.status_code == 200, "Request failed. Status code %d." % response.status_code
        rec = json.loads(response.content)
        assert rec["user"] in map(lambda x: x.external_id, User.objects.all()), "User don't exist in cache"
        assert len(rec["recommendations"]) == 5, "Size of recommendation not 5 (%d)" % len(rec["recommendations"])

    def test_liveliness_of_recommendation_size_5(self):
        """
        [recommendation.api.GetRecommendation] Test liveliness for size 5 recommendation (at least 3 different items)
        """
        size = 5
        response = \
            self.client.get("/api/v2/recommend/%d/"
                            "00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961/" % size)

        rec0 = json.loads(response.content)["recommendations"]
        response = \
            self.client.get("/api/v2/recommend/%d/"
                            "00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961/" % size)

        rec1 = json.loads(response.content)["recommendations"]
        measure = 0
        for item in rec1:
            if item in rec0:
                measure += 1
        assert measure < (size/2.), "New recommendation not different enough"

    def test_liveliness_of_recommendation_size_15(self):
        """
        [recommendation.api.GetRecommendation] Test liveliness for size 15 recommendation (at least 8 different items)
        """
        size = 15
        response = \
            self.client.get("/api/v2/recommend/%d/"
                            "00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961/" % size)

        rec0 = json.loads(response.content)["recommendations"]
        response = \
            self.client.get("/api/v2/recommend/%d/"
                            "00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961/" % size)

        rec1 = json.loads(response.content)["recommendations"]
        measure = 0
        for item in rec1:
            if item in rec0:
                measure += 1
        assert measure < (size/2.), "New recommendation not different enough"

    def test_liveliness_of_recommendation_size_25(self):
        """
        [recommendation.api.GetRecommendation] Test liveliness for size 25 recommendation (at least 9 different items)
        """
        size = 25
        response = \
            self.client.get("/api/v2/recommend/%d/"
                            "00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961/" % size)

        rec0 = json.loads(response.content)["recommendations"]
        response = \
            self.client.get("/api/v2/recommend/%d/"
                            "00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961/" % size)

        rec1 = json.loads(response.content)["recommendations"]
        measure = 0
        for item in rec1:
            if item in rec0:
                measure += 1
        assert measure < (size*2./3.), "New recommendation not different enough"

    def test_diversity_on_recommendation_5(self):
        """
        [recommendation.api.GetRecommendation] Test diversity for size 5 recommendation (at least 2/3 of user genres)
        """
        size = 5
        response = \
            self.client.get("/api/v2/recommend/%d/"
                            "00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961/" % size)
        user = User.get_user("00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961")
        user_genres = ItemGenre.genre_in(Item.get_item(item_eid) for item_eid in user.owned_items)
        recommendation_genres = ItemGenre.genre_in(
            Item.get_item(item_eid) for item_eid in json.loads(response.content)["recommendations"]
        )
        less, more = (user_genres, recommendation_genres) if len(user_genres) < len(recommendation_genres) else \
            (recommendation_genres, user_genres)
        measure = 0
        for genre in less:
            if genre in more:
                measure += 1

        assert measure > len(less)*2./3., \
            "Not sufficient genres in recommendation" \
            "(user: %d, recommendation: %d)" % (len(user_genres), len(recommendation_genres))

    def test_diversity_on_recommendation_15(self):
        """
        [recommendation.api.GetRecommendation] Test diversity for size 15 recommendation (at least 1/2 of user genres)
        """
        size = 15
        response = \
            self.client.get("/api/v2/recommend/%d/"
                            "00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961/" % size)
        user = User.get_user("00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961")
        user_genres = ItemGenre.genre_in(Item.get_item(item_id) for item_id in user.owned_items)
        recommendation_genres = ItemGenre.genre_in(
            Item.get_item(item_eid) for item_eid in json.loads(response.content)["recommendations"]
        )
        less, more = (user_genres, recommendation_genres) if len(user_genres) < len(recommendation_genres) else \
            (recommendation_genres, user_genres)
        measure = 0
        for genre in less:
            if genre in more:
                measure += 1

        assert measure > len(less)/2., \
            "Not sufficient genres in recommendation" \
            "(user: %d, recommendation: %d)" % (len(user_genres), len(recommendation_genres))

    def test_diversity_on_recommendation_25(self):
        """
        [recommendation.api.GetRecommendation] Test diversity for size 25 recommendation (at least 2/3 of user genres)
        """
        size = 2501
        response = \
            self.client.get("/api/v2/recommend/%d/"
                            "00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961/" % size)
        user = User.get_user("00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961")
        user_genres = ItemGenre.genre_in(Item.get_item_by_id(item_id) for item_id in user.owned_items)
        recommendation_genres = ItemGenre.genre_in(
            Item.get_item(item_eid) for item_eid in json.loads(response.content)["recommendations"]
        )
        less, more = (user_genres, recommendation_genres) if len(user_genres) < len(recommendation_genres) else \
            (recommendation_genres, user_genres)
        measure = 0
        for genre in less:
            if genre in more:
                measure += 1

        assert measure > len(less)*2./3., \
            "Not sufficient genres in recommendation" \
            "(user: %d, recommendation: %d)" % (len(user_genres), len(recommendation_genres))

