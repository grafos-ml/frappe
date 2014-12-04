#! -*- encoding: utf-8 -*-
"""
This test package is fully dedicated to models module in recommendation app.
"""
__author__ = "joaonrb"

from django.core.cache import get_cache
from django.test import TransactionTestCase
from frappe.models import Item, User, Inventory


ITEMS = [
    {"name": "facemagazine", "external_id": "10001"},
    {"name": "twister", "external_id": "10002"},
    {"name": "gfail", "external_id": "10003"},
    {"name": "appwhat", "external_id": "10004"},
    {"name": "pissedoffbirds", "external_id": "98766"},
]


USERS = [
    {"external_id": "joaonrb", "items": ["10001", "10003", "10004"]},
    {"external_id": "mumas", "items": ["10003", "10004", "98766"]},
    {"external_id": "alex", "items": ["10003"]},
    {"external_id": "rob", "items": ["10003", "10004"]},
    {"external_id": "gabriela", "items": ["10002", "98766"]},
    {"external_id": "ana", "items": []},
    {"external_id": "margarida", "items": ["10001", "98766"]},
]


class TestItems(TransactionTestCase):
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

    def test_add_new_item(self):
        """
        [frappe base models Item] Test add new item
        """
        new_item = Item.objects.create(external_id="33", name="Pokemon Fire Water")
        with self.assertNumQueries(1):
            try:
                cached_new_item = Item.get_item(new_item.external_id)
            except Item.DoesNotExist:
                assert False, "Just created item is not in db"
            assert new_item.name == cached_new_item.name, \
                "New item(%s) name different from the returned from db(%s)" % (new_item.name, cached_new_item.name)
        with self.assertNumQueries(0):
            # Test if after query the database the item stays in cache
            cached_new_item = Item.get_item(new_item.external_id)
            assert new_item.external_id == cached_new_item.external_id, \
                "New item(%s) name different from the returned from cache(%s)" % (new_item.name, cached_new_item.name)

    def test_get_non_existing_items(self):
        """
        [frappe base models Item] Test getting none existing items
        """
        for item_eid in ("5", "40", "547sh", "veqg57g", "lkn6ni6n6ulm5lknulk57nmdjpoNYSDY6"):
            with self.assertRaises(Item.DoesNotExist):
                Item.get_item(item_eid)


class TestUser(TransactionTestCase):
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

    def test_add_new_user(self):
        """
        [frappe base models User] Test add new user
        """
        new_user = User.objects.create(external_id="111111")
        with self.assertNumQueries(1):
            try:
                cached_new_user = User.get_user(new_user.external_id)
            except User.DoesNotExist:
                assert False, "Just created user is not in db"
            assert new_user.external_id == cached_new_user.external_id, \
                "New user(%s) name different from the returned from db(%s)" % (new_user.external_id,
                                                                               cached_new_user.external_id)
        with self.assertNumQueries(0):
            # Test if after query the database the item stays in cache
            cached_new_user = User.get_user(new_user.external_id)
            assert new_user.external_id == cached_new_user.external_id, \
                "New user(%s) name different from the returned from cache(%s)" % (new_user.external_id,
                                                                                  cached_new_user.external_id)

    def test_add_new_item_to_user(self):
        """
        [frappe base models User] Test add user to item

        The insertion of new item in db is not hooked to the cache. For that you have to make it manually.
        """
        new_item = Item.objects.create(external_id="367869", name="Lazy Runner")
        user = User.get_user("joaonrb")
        entry = Inventory.objects.create(user=user, item=new_item)
        self.assertNotIn(entry.item_id, user.owned_items, msg="Item automatically go to cache.")
        User.get_user_items.set(("joaonrb",), user.owned_items.union([entry.item_id]))
        self.assertIn(entry.item_id, user.owned_items, msg="Item still not in cache.")