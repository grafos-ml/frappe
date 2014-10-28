#! -*- encoding: utf-8 -*-
"""
This test package test the diversity
"""
__author__ = "joaonrb"

from random import shuffle
from django.test import TestCase
from django.utils import timezone as dt
from django.core.cache import get_cache
from recommendation.models import Item, User, Inventory
from recommendation.diversity.models import Genre, ItemGenre
from recommendation.diversity.rerankers import SimpleDiversityReRanker

GENRES = [
    {"id": 1, "name": "games"},
    {"id": 2, "name": "message"},
    {"id": 3, "name": "social"},
]


ITEMS = [
    {"id": 1, "name": "facemagazine", "external_id": "10001", "genres": ["social"]},
    {"id": 2, "name": "twister", "external_id": "10002", "genres": ["social"]},
    {"id": 3, "name": "gfail", "external_id": "10003", "genres": ["message"]},
    {"id": 4, "name": "appwhat", "external_id": "10004", "genres": ["social", "message"]},
    {"id": 5, "name": "pissedoffbirds", "external_id": "98766", "genres": ["social", "games"]},
]


USERS = [
    {"id": 1, "external_id": "joaonrb", "items": ["10001", "10003", "10004"]},
    {"id": 2, "external_id": "mumas", "items": ["10003", "10004", "98766"]},
    {"id": 3, "external_id": "alex", "items": ["10003"], "last_apps": ["98766"]},
    {"id": 4, "external_id": "rob", "items": ["10003", "10004"]},
    {"id": 5, "external_id": "gabriela", "items": ["10002", "98766"]},
    {"id": 6, "external_id": "ana", "items": []},
    {"id": 7, "external_id": "margarida", "items": ["10001", "98766"]},
]


class TestLanguageFilter(TestCase):
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
        for genre in GENRES:
            Genre.objects.create(**genre)
        for app in ITEMS:
            item = Item.objects.create(name=app["name"], external_id=app["external_id"])
            for genre in app["genres"]:
                g = Genre.objects.get(name=genre)
                ItemGenre.objects.create(item=item, type=g)
        for u in USERS:
            user = User.objects.create(external_id=u["external_id"])
            for i in u["items"]:
                Inventory.objects.create(user=user, item=Item.get_item_by_external_id(i))
        Genre.load_to_cache()
        ItemGenre.load_to_cache()

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        Inventory.objects.all().delete()
        ItemGenre.objects.all().delete()
        Item.objects.all().delete()
        User.objects.all().delete()
        Genre.objects.all().delete()
        get_cache("default").clear()
        get_cache("local").clear()

    def test_items_language_cache(self):
        """
        [recommendation.diversity.Cache] Test item in genre cache system
        """
        for i in ITEMS:
            item = Item.objects.get(external_id=i["external_id"])
            for gen in item.genres.all():
                assert gen.type.pk in ItemGenre.get_genre_by_item(item.pk), \
                    "Genre %s for item %s is not in cache" % (gen.type, item)

    def test_reranker_diversity(self):
        """
        [recommendation.diversity.ReRanker] Test a diversity re-ranker on recommendation
        """
        diversity = SimpleDiversityReRanker()
        recommendation = [Item.get_item_by_external_id(i).pk for i in ("10001", "10002", "10003", "10004", "98766")]
        shuffle(recommendation)
        for u in USERS:
            user = User.get_user_by_external_id(u["external_id"])
            with self.assertNumQueries(0):
                result = diversity(user=user, recommendation=recommendation[:], size=5)

            new_rec = [aid+1 for aid, _ in sorted(enumerate(result), key=lambda x: x[1], reverse=True)]
            assert len(result) == len(ITEMS), "Recommendation size changed (%d != %s)" % (len(new_rec), len(ITEMS))

    def test_reranker_diversity_no_redundancy(self):
        """
        [recommendation.diversity.ReRanker] Test a diversity re-ranker on recommendation for non redundancy and loss
        """
        diversity = SimpleDiversityReRanker()
        recommendation = [Item.get_item_by_external_id(i).pk for i in ("10001", "10002", "10003", "10004", "98766")]
        shuffle(recommendation)
        for u in USERS:
            user = User.get_user_by_external_id(u["external_id"])
            with self.assertNumQueries(0):
                result = diversity(user=user, recommendation=recommendation[:], size=5)

            new_rec = [aid+1 for aid, _ in sorted(enumerate(result), key=lambda x: x[1], reverse=True)]
            assert len(set(result)) == len(ITEMS), "Recommendation size changed (%d != %s)" % (len(new_rec), len(ITEMS))