#! -*- encoding: utf-8 -*-
"""
Frappe core. This is the place were the request meet the backend
"""
__author__ = "joaonrb"

from django.conf import settings


MAX_FRAPPE_SLOTS = getattr(settings, "MAX_FRAPPE_SLOTS", 100)


class RecommendationCore(object):

    @staticmethod
    def pick_module(user_eid):
        user_value = hash(user_eid) % MAX_FRAPPE_SLOTS
        return RecommendationCore.get_module(user_value)