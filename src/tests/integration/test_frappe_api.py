#! -*- encoding: utf-8 -*-
"""
This test package test the recommendation api
"""
__author__ = "joaonrb"

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
import recommendation
from recommendation.management.commands import fill, modelcrafter
from recommendation.models import Item, User, Inventory, Matrix, TensorCoFi, Popularity
from recommendation.language.models import Locale, ItemLocale, UserLocale, Region, UserRegion, ItemRegion
from recommendation.diversity.models import ItemGenre, Genre
from recommendation.simple_logging.models import LogEntry


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
        path = resource_filename(recommendation.__name__, "/")
        fill.FillTool({"items": True, "--mozilla": True, "prod": True}).load()
        fill.FillTool({"users": True, "--mozilla": True, "<path>": path+"data/user"}).load()
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
        ItemRegion.objects.all().delete()
        UserRegion.objects.all().delete()
        Region.objects.all().delete()
        ItemGenre.objects.all().delete()
        Genre.objects.all().delete()
        ItemLocale.objects.all().delete()
        UserLocale.objects.all().delete()
        Locale.objects.all().delete()
        Inventory.objects.all().delete()
        Item.objects.all().delete()
        User.objects.all().delete()
        Matrix.objects.all().delete()
        get_cache("default").clear()

    def test_recommendation_get_user_item(self):
        """
        [recommendation.api.GetUserItems] Test Get user items
        """
        response = \
            self.client.get("/api/v2/user-items/006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173/")
        assert response.status_code == 200, "Request failed. Status code %d." % response.status_code
        its = json.loads(response.content)
        assert its["user"] == "006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173", "User is not correct"
        assert len(its["items"]) == 1, "Owned items should be 1"
        assert its["items"][0]["external_id"] == "413346", "Owned item is not 413346"

    def test_recommendation_acquire_new_item(self):
        """
        [recommendation.api.GetUserItems] Test acquire new item
        """
        user = User.get_user_by_external_id("00504e6196ab5fa37ae7450dad99d031a80c50ef4b762c15151a2e4e92c64e0b")
        items = user.owned_items
        response = self.client.post(
            "/api/v2/user-items/00504e6196ab5fa37ae7450dad99d031a80c50ef4b762c15151a2e4e92c64e0b/",
            {"item_to_acquire": "504343"}
        )
        sleep(0.8)
        assert response.status_code == 200, "Request failed. Status code %d." % response.status_code
        assert len(user.owned_items) == len(items)+1, "Owned items should be %d(%d)" % (len(items)+1,
                                                                                        len(user.owned_items))
        assert Item.get_item_by_external_id("504343").pk in user.owned_items.keys(), "New item not in owned items"

    def test_recommendation_update_user(self):
        """
        [recommendation.api.GetUserItems] Test update user items
        """
        response = self.client.put(
            "/api/v2/user-items/00504e6196ab5fa37ae7450dad99d031a80c50ef4b762c15151a2e4e92c64e0b/",
            '{"user_items": ["504343", "413346"]}',
            content_type="application/json"
        )
        sleep(0.8)
        user = User.get_user_by_external_id("00504e6196ab5fa37ae7450dad99d031a80c50ef4b762c15151a2e4e92c64e0b")
        assert response.status_code == 200, "Request failed. Status code %d." % response.status_code
        assert len(user.owned_items) == 2, "Owned items should be 3(%d)" % len(user.owned_items)
        assert Item.get_item_by_external_id("504343").pk in user.owned_items, "New item not in owned items"
        assert Item.get_item_by_external_id("413346").pk in user.owned_items, "New item not in owned items"

    def test_recommendation_remove_new_item(self):
        """
        [recommendation.api.GetUserItems] Test remove old item
        """
        response = self.client.delete(
            "/api/v2/user-items/006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173/",
            "item_to_remove=413346",
            content_type="application/x-www-form-urlencoded; charset=UTF-8"
        )
        sleep(0.8)
        assert response.status_code == 200, "Request failed. Status code %d. Message: %s" % \
                                            (response.status_code, json.loads(response.content).get("error", ""))
        assert len(User.get_user_by_external_id(
            "006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173").owned_items) == 0, \
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
        path = resource_filename(recommendation.__name__, "/")
        fill.FillTool({"items": True, "--mozilla": True, "prod": True}).load()
        fill.FillTool({"users": True, "--mozilla": True, "<path>": path+"data/user"}).load()
        modelcrafter.main("train", "popularity")
        modelcrafter.main("train", "tensorcofi")
        # Load user and items
        Item.load_to_cache()
        User.load_to_cache()
        # Load main models
        Popularity.load_to_cache()
        TensorCoFi.load_to_cache()
        Locale.load_to_cache()
        Region.load_to_cache()
        Genre.load_to_cache()
        cls.client = Client()

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        ItemRegion.objects.all().delete()
        UserRegion.objects.all().delete()
        Region.objects.all().delete()
        ItemGenre.objects.all().delete()
        Genre.objects.all().delete()
        ItemLocale.objects.all().delete()
        UserLocale.objects.all().delete()
        Locale.objects.all().delete()
        Inventory.objects.all().delete()
        Item.objects.all().delete()
        User.objects.all().delete()
        Matrix.objects.all().delete()
        get_cache("default").clear()

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
        assert abs(t[0] - tfm[0]) < 0.15, \
            "Difference between testfm implementation and frappe is to high (%f, %f)" % (t[0], tfm[0])

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

    def test_user_genres_in_recommendation_size_5(self):
        """
        [recommendation.api.GetRecommendation] At least 2 of the top genres in the size 5 recommendation
        """
        get_cache("default").clear()
        LogEntry.objects.all().delete()
        size = 5
        response = \
            self.client.get("/api/v2/recommend/%d/"
                            "00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961/" % size)
        user_id = User.get_user_id_by_external_id("00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961")

        user_genres = sorted(ItemGenre.genre_in(
            Item.get_item_by_id(item_id) for item_id in User.get_user_items(user_id)
        ).items(), key=lambda x: x[1], reverse=True)
        recommendation_genres = ItemGenre.genre_in(
            Item.get_item_by_external_id(item_eid) for item_eid in json.loads(response.content)["recommendations"]
        )
        measure = []
        for no, (genre, _) in enumerate(user_genres[:int(size)], start=1):
            if genre not in recommendation_genres:
                measure.append(no)
        assert len(measure) < 4, "Major genres failing by index: %s." \
                                 "\nUser %s" \
                                 "\nRecommendation %s" % (
            measure, user_genres, [ItemGenre.genre_in([Item.get_item_by_external_id(item)])
                                   for item in json.loads(response.content)["recommendations"]])

    def test_user_genres_in_recommendation_size_15(self):
        """
        [recommendation.api.GetRecommendation] At least 8 of the top genres in the size 15 recommendation
        """
        get_cache("default").clear()
        LogEntry.objects.all().delete()
        size = 15
        response = \
            self.client.get("/api/v2/recommend/%d/"
                            "00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961/" % size)
        user_id = User.get_user_id_by_external_id("00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961")

        user_genres = sorted(ItemGenre.genre_in(
            Item.get_item_by_id(item_id) for item_id in User.get_user_items(user_id)
        ).items(), key=lambda x: x[1], reverse=True)
        recommendation_genres = ItemGenre.genre_in(
            Item.get_item_by_external_id(item_eid) for item_eid in json.loads(response.content)["recommendations"]
        )
        measure = []
        for no, (genre, _) in enumerate(user_genres[:int(size)], start=1):
            if genre not in recommendation_genres:
                measure.append(no)
        assert len(measure) < 7, "Major genres failing by index: %s." \
                                 "\nUser %s" \
                                 "\nRecommendation %s" % (
            measure, user_genres, [ItemGenre.genre_in([Item.get_item_by_external_id(item)])
                                   for item in json.loads(response.content)["recommendations"]])

    def test_user_genres_in_recommendation_size_25(self):
        """
        [recommendation.api.GetRecommendation] At least 19 of the top genres in the size 25 recommendation
        """
        get_cache("default").clear()
        LogEntry.objects.all().delete()
        size = 25
        response = \
            self.client.get("/api/v2/recommend/%d/"
                            "00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961/" % size)
        user_id = User.get_user_id_by_external_id("00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961")

        user_genres = sorted(ItemGenre.genre_in(
            Item.get_item_by_id(item_id) for item_id in User.get_user_items(user_id)
        ).items(), key=lambda x: x[1], reverse=True)
        recommendation_genres = ItemGenre.genre_in(
            Item.get_item_by_external_id(item_eid) for item_eid in json.loads(response.content)["recommendations"]
        )
        measure = []
        for no, (genre, _) in enumerate(user_genres[:int(size)], start=1):
            if genre not in recommendation_genres:
                measure.append(no)
        assert len(measure) < 6, "Major genres failing by index: %s." \
                                 "\nUser %s" \
                                 "\nRecommendation %s" % (
            measure, user_genres, [ItemGenre.genre_in([Item.get_item_by_external_id(item)])
                                   for item in json.loads(response.content)["recommendations"]])

    def test_diversity_on_recommendation_15(self):
        """
        [recommendation.api.GetRecommendation] Test diversity for size 15 recommendation (at least 1/2 of user genres)
        """
        size = 15
        response = \
            self.client.get("/api/v2/recommend/%d/"
                            "00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961/" % size)
        user_id = User.get_user_id_by_external_id("00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961")
        user_genres = ItemGenre.genre_in(
            Item.get_item_by_id(item_id) for item_id in User.get_user_items(user_id)
        )
        recommendation_genres = ItemGenre.genre_in(
            Item.get_item_by_external_id(item_eid) for item_eid in json.loads(response.content)["recommendations"]
        )
        less, more = (user_genres, recommendation_genres) if len(user_genres) < len(recommendation_genres) else \
            (recommendation_genres, user_genres)
        measure = 0
        for genre in less:
            if genre in more:
                measure += 1

        assert measure > len(less)/2., \
            "Not sufficient genres in recommendation" \
            "(user: %d, recommendation: %d, similarity: %d)" % (len(user_genres), len(recommendation_genres), measure)

    def test_diversity_on_recommendation_25(self):
        """
        [recommendation.api.GetRecommendation] Test diversity for size 25 recommendation (at least 2/3 of user genres)
        """
        size = 25
        response = \
            self.client.get("/api/v2/recommend/%d/"
                            "00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961/" % size)
        user_id = User.get_user_id_by_external_id("00b65a359307654a7deee7c71a7563d2816d6b7e522377a66aaefe8848da5961")
        user_genres = ItemGenre.genre_in(
            Item.get_item_by_id(item_id) for item_id in User.get_user_items(user_id)
        )
        recommendation_genres = ItemGenre.genre_in(
            Item.get_item_by_external_id(item_eid) for item_eid in json.loads(response.content)["recommendations"]
        )
        less, more = (user_genres, recommendation_genres) if len(user_genres) < len(recommendation_genres) else \
            (recommendation_genres, user_genres)
        measure = 0
        for genre in less:
            if genre in more:
                measure += 1

        assert measure > len(less)*2./3., \
            "Not sufficient genres in recommendation" \
            "(user: %d, recommendation: %d, similarity: %d)" % (len(user_genres), len(recommendation_genres), measure)

    def test_filter_owned(self):
        """
        [recommendation.api.GetRecommendation] Test filter owned item
        """
        size = 50
        for user in User.objects.all():
            response = self.client.get("/api/v2/recommend/%d/%s/" %(size, user.external_id))
            recommendation = json.loads(response.content)["recommendations"]
            for item in user.owned_items.values():
                self.assertNotIn(item.external_id, recommendation, "User %s item %s is in recommendation" % (
                    user.external_id, item.external_id))
