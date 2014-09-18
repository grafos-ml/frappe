#! -*- encoding: utf-8 -*-
"""
This test package test the diversity
"""
__author__ = "joaonrb"

from random import shuffle
from django.test import TestCase
from django.utils import timezone as dt
from recommendation.models import Item, User, Inventory
from recommendation.diversity.models import Genre, ItemGenre
from recommendation.diversity.rerankers import SimpleDiversityReRanker

GENRES = [
    {"name": "games"},
    {"name": "message"},
    {"name": "social"},
]


ITEMS = [
    {"name": "facemagazine", "external_id": "10001", "genres": ["social"]},
    {"name": "twister", "external_id": "10002", "genres": ["social"]},
    {"name": "gfail", "external_id": "10003", "genres": ["message"]},
    {"name": "appwhat", "external_id": "10004", "genres": ["social", "message"]},
    {"name": "pissedoffbirds", "external_id": "98766", "genres": ["social", "games"]},
]


USERS = [
    {"external_id": "joaonrb", "items": ["10001", "10003", "10004"]},
    {"external_id": "mumas", "items": ["10003", "10004", "98766"]},
    {"external_id": "alex", "items": ["10003"], "last_apps": ["98766"]},
    {"external_id": "rob", "items": ["10003", "10004"]},
    {"external_id": "gabriela", "items": ["10002", "98766"]},
    {"external_id": "ana", "items": []},
    {"external_id": "margarida", "items": ["10001", "98766"]},
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
                Inventory.objects.create(user=user, item=Item.get_item_by_external_id(i), acquisition_date=dt.now())

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        ItemGenre.objects.all().delete()
        Item.objects.all().delete()
        User.objects.all().delete()
        Genre.objects.all().delete()

    def test_items_language_cache(self):
        """
        [recommendation.diversity.Cache] Test item in genre cache system
        """
        for i in ITEMS:
            item = Item.objects.get(external_id=i["external_id"])
            for gen in item.genres.all():
                assert gen.type.pk in ItemGenre.genre_by_item[item.pk], \
                    "Genre %s for item %s is not in cache" % (gen.type, item)

    def test_reranker_diversity(self):
        """
        [recommendation.diversity.ReRanker] Test a diversity re-ranker on recommendation
        """
        diversity = SimpleDiversityReRanker()
        recommendation = [Item.get_item_id_by_external_id(i) for i in ("10001", "10002", "10003", "10004", "98766")]
        shuffle(recommendation)
        for u in USERS:
            user = User.user_by_external_id[u["external_id"]]
            result = diversity(user=user, recommendation=recommendation[:], size=5)

            new_rec = [aid+1 for aid, _ in sorted(enumerate(result), key=lambda x: x[1], reverse=True)]
            assert len(result) == len(ITEMS), "Recommendation size changed (%d != %s)" % (len(new_rec), len(ITEMS))

    def test_reranker_diversity_no_redundancy(self):
        """
        [recommendation.diversity.ReRanker] Test a diversity re-ranker on recommendation for non redundancy snd loss
        """
        diversity = SimpleDiversityReRanker()
        recommendation = [Item.get_item_id_by_external_id(i) for i in ("10001", "10002", "10003", "10004", "98766")]
        shuffle(recommendation)
        for u in USERS:
            user = User.user_by_external_id[u["external_id"]]
            result = diversity(user=user, recommendation=recommendation[:], size=5)

            new_rec = [aid+1 for aid, _ in sorted(enumerate(result), key=lambda x: x[1], reverse=True)]
            assert len(set(result)) == len(ITEMS), "Recommendation size changed (%d != %s)" % (len(new_rec), len(ITEMS))