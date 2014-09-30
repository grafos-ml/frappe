#! -*- encoding: utf-8 -*-
"""
This test package test the filter owned items
"""
__author__ = "joaonrb"

import numpy as np
import random
from django.test import TestCase
from django.utils import timezone as dt
from django.core.cache import get_cache
from recommendation.models import Item, User, Inventory
from recommendation.filter_owned.filters import FilterOwned


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


class TestFilterOwnedItems(TestCase):
    """
    Test suite for recommendation filter for owned items

    Test:
        - Filter recommendation
    """

    @classmethod
    def setup_class(cls, *args, **kwargs):
        """
        Put elements in db
        """
        for app in ITEMS:
            Item.objects.create(**app)
        for u in USERS:
            user = User.objects.create(external_id=u["external_id"])
            for i in u["items"]:
                Inventory.objects.create(user=user, item=Item.get_item_by_external_id(i), acquisition_date=dt.now())

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        Inventory.objects.all().delete()
        Item.objects.all().delete()
        User.objects.all().delete()
        get_cache("default").clear()
        get_cache("local").clear()

    def test_filter_owned(self):
        """
        [recommendation.filter.OwnedIems] Test a filter owned items on recommendation
        """
        rfilter = FilterOwned()
        recommendation = [random.random() for _ in range(len(ITEMS))]
        for u in USERS:
            user = User.get_user_by_external_id(u["external_id"])
            with self.assertNumQueries(0):
                result = rfilter(user, np.array(recommendation[:]))
            new_rec = [aid+1 for aid, _ in sorted(enumerate(result), key=lambda x: x[1], reverse=True)]
            n = len(user.owned_items)
            for item in user.owned_items:
                assert item in new_rec[0-n:], "Item %d is not in the last in recommendation %s. User owned items %s" % \
                    (item, new_rec, list(user.owned_items.keys()))

    def test_recommendation_size_after_filter(self):
        """
        [recommendation.filter.OwnedIems] Test the size of the recommendation after the filter
        """
        rfilter = FilterOwned()
        recommendation = [random.random() for _ in range(len(ITEMS))]
        for u in USERS:
            user = User.get_user_by_external_id(u["external_id"])
            with self.assertNumQueries(0):
                result = rfilter(user, np.array(recommendation[:]))
            new_rec = [aid+1 for aid, _ in sorted(enumerate(result), key=lambda x: x[1], reverse=True)]
            assert len(new_rec) == len(ITEMS), "Recommendation size changed (%d != %s)" % (len(new_rec), len(ITEMS))
