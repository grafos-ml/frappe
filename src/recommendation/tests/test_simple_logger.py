#! -*- encoding: utf-8 -*-
"""
This test package simple logger
"""
__author__ = "joaonrb"

import time
from django.test import TestCase
from django.utils import timezone as dt
from recommendation.models import Item, User, Inventory
from recommendation.simple_logging.models import LogEntry
from recommendation.simple_logging.decorators import LogEvent


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
                Inventory.objects.create(user=user, item=Item.item_by_external_id[i], acquisition_date=dt.now())

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        """
        Take elements from db
        """
        Item.objects.all().delete()
        User.objects.all().delete()
        LogEntry.objects.all().delete()

    def test_recommendation_logging(self):
        """
        [recommendation.decorator.SimpleLogger] Test if a recommendation is logged
        """
        logger = LogEvent(LogEvent.RECOMMEND)
        user = User.user_by_external_id["joaonrb"]
        recommendation = logger(lambda user: ["10001", "10002", "10003", "10004", "98766"])(user)
        logs = list(LogEntry.objects.filter(user=user, type=logger.RECOMMEND).order_by("-timestamp", "value"))

        assert len(logs) == 5, "Number of register is not correct %s" % logs
