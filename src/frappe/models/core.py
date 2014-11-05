#! -*- encoding: utf-8 -*-
"""
Models for core recommendation slots
"""
__author__ = "joaonrb"

import random
import itertools
from django.utils.translation import ugettext as _
from django.db import models
from django.conf import settings
from frappe.models.module import Module
from frappe.decorators import Cached

MAX_FRAPPE_SLOTS = getattr(settings, "MAX_FRAPPE_SLOTS", 100)


class Slot(models.Model):
    """
    Slot to frappe recommendation modules
    """

    slot = models.SmallIntegerField(_("slot"), max_length=len(str(MAX_FRAPPE_SLOTS))-1, unique=True)
    module = models.ForeignKey(Module, verbose_name=_("module"))

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
        return Slot.objects.get(slot=slot).module_id

    @staticmethod
    def update_modules():
        """
        Update slots positions for modules
        """
        modules = {}
        sum_of_scores = 0.
        for module_id, frequency_score in Module.objects.filter(active=True).values_list("pk", "frequency_score"):
            modules[module_id] = frequency_score*MAX_FRAPPE_SLOTS
            sum_of_scores += frequency_score

        slots = list(itertools.chain(*([module_id]*int(score/sum_of_scores) for module_id, score in modules.items())))
        random.shuffle(slots)
        db_slots = {slot.pk: slot for slot in Slot.objects.all()}
        for i in xrange(MAX_FRAPPE_SLOTS):
            module_id = slots[i]
            try:
                db_slots[i].module_id = module_id
            except KeyError:
                db_slots[i] = Slot(slot=i, module_id=module_id)
        Slot.objects.bulk_create(db_slots.values())