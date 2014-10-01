#! -*- encoding: utf-8 -*-
"""
This test package test the filter language based
"""
__author__ = "joaonrb"

import numpy as np
import random
from time import sleep
from django.test import TestCase
from django.utils import timezone as dt
from django.core.cache import get_cache
from recommendation.models import Item, User, Inventory
from recommendation.language.models import Locale, ItemLocale, UserLocale
from recommendation.language.filters import SimpleLocaleFilter

LANGUAGES = [
    {"language_code": "pt", "country_code": "pt", "name": "Portuguese"},
    {"language_code": "en", "country_code": "en", "name": "English"},
    {"language_code": "fr", "country_code": "fr", "name": "French"}
]


ITEMS = [
    {"id": 1, "name": "facemagazine", "external_id": "10001", "languages": ["pt", "fr"]},
    {"id": 2, "name": "twister", "external_id": "10002", "languages": ["en", "pt"]},
    {"id": 3, "name": "gfail", "external_id": "10003", "languages": ["en", "pt", "fr"]},
    {"id": 4, "name": "appwhat", "external_id": "10004", "languages": ["en", "fr"]},
    {"id": 5, "name": "pissedoffbirds", "external_id": "98766", "languages": ["pt"]},
]


USERS = [
    {"id": 1, "external_id": "joaonrb", "items": ["10001", "10003", "10004"], "languages": ["en", "pt"],
     "last_apps": []},
    {"id": 2, "external_id": "mumas", "items": ["10003", "10004", "98766"], "languages": ["en", "fr"],
     "last_apps": ["98766"]},
    {"id": 3, "external_id": "alex", "items": ["10003"], "languages": ["en", "fr"], "last_apps": ["98766"]},
    {"id": 4, "external_id": "rob", "items": ["10003", "10004"], "languages": ["en"], "last_apps": ["10001", "98766"]},
    {"id": 5, "external_id": "gabriela", "items": ["10002", "98766"], "languages": ["en", "pt", "fr"], "last_apps": []},
    {"id": 6, "external_id": "ana", "items": [], "languages": ["fr"], "last_apps": ["10002", "98766"]},
    {"id": 7, "external_id": "margarida", "items": ["10001", "98766"], "languages": ["pt", "fr"], "last_apps": []},
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
        for language in LANGUAGES:
            Locale.objects.create(**language)
        for app in ITEMS:
            item = Item.objects.create(id=app["id"], name=app["name"], external_id=app["external_id"])
            for language in app["languages"]:
                l = Locale.objects.get(country_code=language)
                ItemLocale.objects.create(locale=l, item=item)
        for u in USERS:
            user = User.objects.create(id=u["id"], external_id=u["external_id"])
            for i in u["items"]:
                Inventory.objects.create(user=user, item=Item.get_item_by_external_id(i), acquisition_date=dt.now())
            for language in u["languages"]:
                l = Locale.objects.get(country_code=language)
                UserLocale.objects.create(locale=l, user=user)
        Locale.load_to_cache()

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        UserLocale.objects.all().delete()
        Locale.objects.all().delete()
        Inventory.objects.all().delete()
        Item.objects.all().delete()
        User.objects.all().delete()
        get_cache("default").clear()
        get_cache("local").clear()

    def test_users_language_cache(self):
        """
        [recommendation.filter.Language] Test user in language cache system
        """
        for u in USERS:
            user = User.objects.get(external_id=u["external_id"])
            for loc in user.locales.all():
                assert loc.locale_id in Locale.get_user_locales(user.pk), \
                    "Locale %s for user %s is not in cache (%s)" % (loc, user, Locale.get_user_locales(user.pk))

    def test_items_language_cache(self):
        """
        [recommendation.filter.Language] Test item in language cache system
        """
        for i in ITEMS:
            item = Item.objects.get(external_id=i["external_id"])
            for loc in item.locales.all():
                assert loc.locale_id in Locale.get_item_locales(item.pk), \
                    "Locale %s for item %s is not in cache (%s)" % (loc, item, Locale.get_item_locales(item.pk))

    def test_filter_language(self):
        """
        [recommendation.filter.Language] Test a language filter on recommendation
        """
        rfilter = SimpleLocaleFilter()
        recommendation = [random.random() for _ in range(len(ITEMS))]
        app_rec = [Item.get_item_by_id(aid+1).external_id
                   for aid, _ in sorted(enumerate(recommendation), key=lambda x: x[1], reverse=True)]
        for u in USERS:
            user = User.get_user_by_external_id(u["external_id"])
            with self.assertNumQueries(0):
                result = rfilter(user, np.array(recommendation[:]))
            new_rec = [Item.get_item_by_id(aid+1).external_id
                       for aid, _ in sorted(enumerate(result), key=lambda x: x[1], reverse=True)]
            n = len(u["last_apps"])
            if n == 0:
                assert new_rec == app_rec, \
                    "Recommendation is not the same when not apps to filter(%s != %s)" % (new_rec, app_rec)
            else:
                for item in u["last_apps"]:
                    assert item in new_rec[0-n:], \
                        "Item %s for user %s is not in the last in recommendation %s. Items filtered %s." % \
                        (item, user, new_rec, list(u["last_apps"]))

    def test_recommendation_size_after_filter(self):
        """
        [recommendation.filter.Language] Test the size of the recommendation after the filter
        """
        rfilter = SimpleLocaleFilter()
        recommendation = [random.random() for _ in range(len(ITEMS))]
        for u in USERS:
            user = User.get_user_by_external_id(u["external_id"])
            with self.assertNumQueries(0):
                result = rfilter(user, np.array(recommendation[:]))
            new_rec = [aid+1 for aid, _ in sorted(enumerate(result), key=lambda x: x[1], reverse=True)]
            assert len(new_rec) == len(ITEMS), "Recommendation size changed (%d != %s)" % (len(new_rec), len(ITEMS))