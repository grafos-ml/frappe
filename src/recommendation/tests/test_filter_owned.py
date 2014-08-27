#! -*- encoding: utf-8 -*-
"""
This test package test the filter owned items
"""
__author__ = "joaonrb"

import json
import pandas as pd
import numpy as np
from pkg_resources import resource_filename
from django.test import TestCase
from django.test.client import Client, MULTIPART_CONTENT
from testfm.evaluation import Evaluator
from testfm.models.tensorcofi import PyTensorCoFi
import recommendation
from recommendation.management.commands import fill, modelcrafter
from recommendation.models import Item, User, Inventory, Matrix, TensorCoFi, Popularity


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


class TestFilterOwnedItems(TestCase):
    """
    Test suite for recommendation filter for owned items

    Test:
        - Filter recommendation
    """