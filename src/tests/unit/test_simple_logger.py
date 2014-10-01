#! -*- encoding: utf-8 -*-
"""
This test package simple logger
"""
__author__ = "joaonrb"

import numpy as np
import random
import unittest as un
import time
from random import shuffle
from django.test import TestCase
from django.utils import timezone as dt
from django.conf import settings
from django.core.cache import get_cache
from recommendation.models import Item, User, Inventory
from recommendation.simple_logging.models import LogEntry, LOGGER_MAX_LOGS
from recommendation.simple_logging.decorators import LogEvent
from recommendation.simple_logging.filters import SimpleLogFilter


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


class TestSimpleLoggerDecorator(TestCase):
    """
    Test suite for recommendation simple logger decorators

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
        time.sleep(1.)

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        LogEntry.objects.all().delete()
        Inventory.objects.all().delete()
        Item.objects.all().delete()
        User.objects.all().delete()
        get_cache("default").clear()
        get_cache("local").clear()

    def test_recommendation_logging(self):
        """
        [recommendation.decorator.SimpleLogger] Test if a recommendation is logged
        """
        logger = LogEvent(LogEvent.RECOMMEND)
        user = User.get_user_by_external_id("joaonrb")
        recommendation = [Item.get_item_by_external_id(i).pk for i in ("10001", "10002", "10003", "10004", "98766")]
        recommendation = logger(lambda user: recommendation)(user=user)
        time.sleep(1.)
        logs = list(LogEntry.objects.filter(user=user, type=logger.RECOMMEND).order_by("value"))
        assert len(logs) == 5, "Number of register is not correct %s" % logs
        logs_iter = iter(logs)
        for i, item in enumerate(recommendation, start=1):
            log = logs_iter.next()
            assert item == log.item.pk, "The item in position %d is not the same that in recommendation " \
                                        "(%s != %s)" % (i, item, log.item.external_id)
            assert i == log.value, "The item in position %d do not have the right value. (%d)" % (i, log.value)

    def test_click_logging(self):
        """
        [recommendation.decorator.SimpleLogger] Test if a clicked item is logged
        """
        logger = LogEvent(LogEvent.CLICK)
        user = User.get_user_by_external_id("joaonrb")
        logger(lambda uid, iid: None)(user, Item.get_item_by_external_id("10004"))
        time.sleep(1.)
        logs = list(LogEntry.objects.filter(user=user, type=logger.CLICK))
        assert len(logs) == 1, "Number of register is not correct %s" % logs
        assert "10004" == logs[0].item.external_id, \
            "The item in log is incorrect(1004 != %s)" % logs[0].item.external_id

    def test_remove_logging(self):
        """
        [recommendation.decorator.SimpleLogger] Test if a removed item is logged
        """
        logger = LogEvent(LogEvent.REMOVE)
        user = User.get_user_by_external_id("joaonrb")
        logger(lambda uid, iid: None)(user, Item.get_item_by_external_id("10004"))
        time.sleep(1.)
        logs = list(LogEntry.objects.filter(user=user, type=logger.REMOVE))
        assert len(logs) == 1, "Number of register is not correct %s" % logs
        assert "10004" == logs[0].item.external_id, \
            "The item in log is incorrect(1004 != %s)" % logs[0].item.external_id

    def test_acquire_logging(self):
        """
        [recommendation.decorator.SimpleLogger] Test if a acquired item is logged
        """
        logger = LogEvent(LogEvent.ACQUIRE)
        user = User.get_user_by_external_id("joaonrb")
        logger(lambda uid, iid: None)(user, Item.get_item_by_external_id("10004"))
        time.sleep(1.)
        logs = list(LogEntry.objects.filter(user=user, type=logger.ACQUIRE))
        assert len(logs) == 1, "Number of register is not correct %s" % logs
        assert "10004" == logs[0].item.external_id, \
            "The item in log is incorrect(1004 != %s)" % logs[0].item.external_id


class TestSimpleLoggerCache(TestCase):
    """
    Test suite for recommendation simple logger cache

    Test:
        - cache max
        - cache results
    """

    @classmethod
    def setup_class(cls, *args, **kwargs):
        """
        Put elements in db
        """
        logger = LogEvent(LogEvent.RECOMMEND)
        for app in ITEMS:
            Item.objects.create(**app)
        for u in USERS:
            user = User.objects.create(external_id=u["external_id"])
            for i in u["items"]:
                Inventory.objects.create(user=user, item=Item.get_item_by_external_id(i), acquisition_date=dt.now())
            for _ in range(3):
                recommendation = [Item.get_item_by_external_id(i).pk
                                  for i in ("10001", "10002", "10003", "10004", "98766")]
                shuffle(recommendation)
                logger(lambda user: recommendation)(user=user)
        time.sleep(1.)

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        Item.objects.all().delete()
        User.objects.all().delete()
        LogEntry.objects.all().delete()

    @un.skipIf(not settings.TESTING_MODE, "Testing mode is not set to true")
    def test_max_log_is_10(self):
        """
        [recommendation.cache.SimpleLogger] Test if the cache limit in debug mode is 10
        """
        assert LOGGER_MAX_LOGS == 10, "Log cache limit is not set to 10"

    @un.skipIf(not settings.TESTING_MODE, "Testing mode is not set to true")
    def test_size_of_logs_in_cache(self):
        """
        [recommendation.cache.SimpleLogger] Test size of cache is 10 for all users in system
        """
        for user in USERS:
            user = User.get_user_by_external_id(user["external_id"])
            assert len(LogEntry.get_logs_for(user.pk)) == 10, \
                "logs size are bigger than predicted (%s != 10)" % len(LogEntry.get_logs_for(user.pk))


class TestFilterByLog(TestCase):
    """
    Test suite for recommendation filter for log system

    Test:
        - Filter recommendation
    """

    @classmethod
    def setup_class(cls, *args, **kwargs):
        """
        Put elements in db
        """
        logger = LogEvent(LogEvent.RECOMMEND)
        for app in ITEMS:
            Item.objects.create(**app)
        for u in USERS:
            user = User.objects.create(external_id=u["external_id"])
            for i in u["items"]:
                Inventory.objects.create(user=user, item=Item.get_item_by_external_id(i), acquisition_date=dt.now())
            for _ in range(3):
                recommendation = [Item.get_item_by_external_id(i).pk
                                  for i in ("10001", "10002", "10003", "10004", "98766")]
                shuffle(recommendation)
                logger(lambda user: recommendation)(user=user)
        time.sleep(1.)

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        Item.objects.all().delete()
        User.objects.all().delete()
        LogEntry.objects.all().delete()

    def test_recommendation_size_after_filter(self):
        """
        [recommendation.filter.SimpleLog] Test the size of the recommendation after the filter
        """
        rfilter = SimpleLogFilter()
        recommendation = [random.random() for _ in range(len(ITEMS))]
        for u in USERS:
            user = User.get_user_by_external_id(u["external_id"])
            with self.assertNumQueries(0):
                result = rfilter(user, recommendation=np.array(recommendation[:]))
            new_rec = [aid+1 for aid, _ in sorted(enumerate(result), key=lambda x: x[1], reverse=True)]
            assert len(new_rec) == len(ITEMS), "Recommendation size changed (%d != %s)" % (len(new_rec), len(ITEMS))