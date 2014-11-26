#! -* encoding: utf8 -*-
"""
Filter items that don't exist in database
"""

from __future__ import division, absolute_import, print_function
import numpy as np
from django.db import models
from recommendation.decorators import Cached
from recommendation.models import Item

__author__ = "joaonrb"


class FilterNoneItems(object):
    """
    Filter items in database that don't exist in database
    """

    @staticmethod
    @Cached()
    def get_none_items():
        n = Item.objects.aggregate(max=models.Max("pk"))["max"]
        none_items = np.zeros((n,), dtype=np.float32)
        items = [item_id - 1 for item_id, in Item.objects.all().order_by("pk").values_list("pk")]
        for i in range(n):
            if i == items[0]:
                items.pop(0)
            else:
                none_items[i] = float("-inf")
        return none_items

    def __call__(self, user, recommendation, *args, **kwargs):
        return recommendation + self.get_none_items()[:len(recommendation)]
