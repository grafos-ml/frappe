#! -*- encoding: utf-8 -*-
"""
Frappe core. This is the place were the request meet the backend
"""
__author__ = "joaonrb"

from django.conf import settings
from frappe.models.core import Slot
from frappe.models.module import Module


MAX_FRAPPE_SLOTS = getattr(settings, "MAX_FRAPPE_SLOTS", 100)


class RecommendationCore(object):

    @staticmethod
    def pick_module(user_eid):
        user_slot = hash(user_eid) % MAX_FRAPPE_SLOTS
        return RecommendationCore.get_module(user_slot)

    @staticmethod
    def get_module(slot):
        return Module.get_module(Slot.get_module(slot))