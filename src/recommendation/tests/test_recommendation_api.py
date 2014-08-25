#! -*- encoding: utf-8 -*-
"""
This test package test the recommendation api
"""
__author__ = "joaonrb"

import unittest as ut
import json
from pkg_resources import resource_filename
from django.test import TestCase
from django.test.client import Client
from django.core.cache import get_cache
from django.utils import timezone as dt
import recommendation
from recommendation.management.commands import fill, modelcrafter
from recommendation.models import Item, User, Matrix, TensorCoFi, Popularity


class TestRecommendation(TestCase):
    """
    Test suite for recommendation system

    Test:
        - Get recommendation
        - Test recommendation against test.fm results
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
        Item.objects.all().delete()
        User.objects.all().delete()
        Matrix.objects.all().delete()

    def test_get_recommendation(self):
        """
        [recommendation.api.GetRecommendation] Get recommendation as json
        """
        response = self.client.get("/api/v2/recommend/5/")
        assert response.status_code == 200, "Request failed. Status code %d." % response.status_code