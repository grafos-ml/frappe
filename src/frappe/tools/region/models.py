# -*- encoding=utf-8 -*-
"""
The locale models module. It must contain the locale
"""

from __future__ import division, absolute_import, print_function
import logging
from django.db import models
from django.utils.translation import ugettext as _
import numpy as np
from frappe.models import Item, User, Module
from frappe.decorators import Cached


__author__ = "joaonrb"


class Region(models.Model):
    """
    Models for region
    """

    name = models.CharField(_("name"), max_length=255, unique=True)
    slug = models.CharField(_("slug"), max_length=25, unique=True)
    items = models.ManyToManyField(Item, verbose_name=_("items"), through="ItemRegion", blank=True, null=True)
    users = models.ManyToManyField(User, verbose_name=_("users"), through="UserRegion", blank=True, null=True)

    class Meta:
        verbose_name = _("region")
        verbose_name_plural = _("regions")

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    @staticmethod
    @Cached(timeout=60*60)
    def get_regions(region_id):
        return Region.objects.get(pk=region_id)

    @staticmethod
    @Cached()
    def get_user_regions(user_eid):
        return [region_id for region_id, in UserRegion.objects.filter(user_id=user_eid).values_list("region_id")]

    @staticmethod
    @Cached()
    def get_item_list_by_region(module_id, region_id):
        module = Module.get_module(module_id)
        items = np.zeros((len(module.listed_items)), dtype=np.bool)  # When sum to a number array bool array is 1 and 0
        for item_id, in ItemRegion.objects.filter(region_id=region_id).values_list("item_id"):
            items[module.items_index[item_id]] = True
        return items

    @staticmethod
    def load_to_cache():
        regions = Region.objects.all()
        for region in regions:
            Region.get_regions.set(region.pk, region)
            logging.debug("Region %s loaded to cache" % region.name)
        logging.debug("%d regions loaded" % len(regions))


class UserRegion(models.Model):
    """
    User regions
    """

    user = models.ForeignKey(User, verbose_name=_("user"), related_name="regions", to_field="external_id")
    region = models.ForeignKey(Region, verbose_name=_("region"))

    class Meta:
        verbose_name = _("user region")
        verbose_name_plural = _("user regions")
        unique_together = ("user", "region")

    def __str__(self):
        return "%s for %s" % (self.region, self.user_id)

    def __unicode__(self):
        return u"%s for %s" % (self.region, self.user_id)

    @staticmethod
    def load_to_cache():
        users = {}
        for user_id, region_id in UserRegion.objects.all().values_list("user_id", "region_id"):
            if user_id in users:
                users[user_id].append(region_id)
            else:
                users[user_id] = [region_id]
        for user_eid, regions in users.items():
            Region.get_user_regions.set((user_eid,), regions)
        logging.debug("%d regions loaded to users" % len(users))


class ItemRegion(models.Model):
    """
    User regions
    """

    item = models.ForeignKey(Item, verbose_name=_("item"), related_name="regions", to_field="external_id")
    region = models.ForeignKey(Region, verbose_name=_("region"))

    class Meta:
        verbose_name = _("item region")
        verbose_name_plural = _("item regions")
        unique_together = ("item", "region")

    def __str__(self):
        return "%s for %s" % (self.region, self.item_id)

    def __unicode__(self):
        return u"%s for %s" % (self.region, self.item_id)

from django.contrib import admin
admin.site.register([Region, ItemRegion, UserRegion])