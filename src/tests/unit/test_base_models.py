#! -*- encoding: utf-8 -*-
"""
This test package is fully dedicated to models module in recommendation app.
"""
__author__ = "joaonrb"

from django.core.cache import get_cache
from django.test import TestCase
from frappe.models import Item, User, Inventory


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


class TestItems(TestCase):
    """
    Test the item models

    ust test:
        - Number of queries when get item by id
        - Number of queries when get item by external id
    """

    @classmethod
    def setup_class(cls, *args, **kwargs):
        """
        Put elements in db
        """
        for app in ITEMS:
            Item.objects.create(**app)
        Item.load_to_cache()

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        Item.objects.all().delete()
        get_cache("default").clear()

    def test_get_item_by_external_id(self):
        """
        [frappe base models Item] Test queries by external id made by getting items and check integrity of that items
        """
        with self.assertNumQueries(0):
            for app in ITEMS:
                item = Item.get_item(app["external_id"])
                assert isinstance(item, Item), "Cached item is not instance of Item."
                assert item.name == app["name"], "Name of the app is not correct"


class TestUser(TestCase):
    """
    Test the user models

    ust test:
        - Number of queries when get item by external id
        - Number of items
        - Number of owned items
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
            for item in u["items"]:
                Inventory.objects.create(user=user, item_id=item)
        Item.load_to_cache()
        User.load_to_cache()
        Inventory.load_to_cache()

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        Inventory.objects.all().delete()
        Item.objects.all().delete()
        User.objects.all().delete()
        get_cache("default").clear()
        get_cache("owned_items").clear()

    def test_get_user(self):
        """
        [frappe base models User] Test queries by external id made by getting user and check integrity of that user
        """
        with self.assertNumQueries(0):
            for u in USERS:
                user = User.get_user(u["external_id"])
                assert isinstance(user, User), "Cached user is not instance of User."

    def test_user_items(self):
        """
        [frappe base models User] Test user items
        """
        with self.assertNumQueries(0):
            for u in USERS:
                user = User.get_user(u["external_id"])
                for i in u["items"]:
                    assert i in user.owned_items, "Item %s is not in user %s" % (i, user.external_id)