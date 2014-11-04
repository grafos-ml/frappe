#! -*- encoding: utf-8 -*-
"""
Models for core recommendation slots
"""
__author__ = "joaonrb"

from django.utils.translation import ugettext as _
from django.db import models
from django.conf import settings
from frappe.models.module import Module
from frappe.decorators import Cached

MAX_FRAPPE_SLOTS = getattr(settings, "MAX_FRAPPE_SLOTS", 100)


class FrappeSlot(models.Model):
    """
    Slot to frappe recommendation modules
    """

    slot = models.SmallIntegerField(_("slot"), max_length=len(str(MAX_FRAPPE_SLOTS))-1, unique=True)
    module = models.ManyToManyField(Module, verbose_name=_("module"))

    class Meta:
        verbose_name = _("slot")
        verbose_name_plural = _("slots")

    @staticmethod
    @Cached(timeout=60)  # Cache refresh each minute
    def get_module(slot):
        """
        Return the module id in this slot
        :param slot: Number of the slot
        :return: Module id
        """
        return FrappeSlot.objects.get(slot=slot).module_id

