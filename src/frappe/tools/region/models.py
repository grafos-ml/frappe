# -*- encoding=utf-8 -*-
"""
The locale models moudle. It must contain the locale
"""
__author__ = "joaonrb"


import click
from django.db import models
from django.utils.translation import ugettext as _
import numpy as np
from frappe.models import Item, User, Module
from frappe.decorators import Cached


class Region(models.Model):
    """
    Models for region
    """

    name = models.CharField(_("name"), max_length=255, unique=True)
    slug = models.CharField(_("slug"), max_length=10, unique=True)
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
    @Cached(cache="local", timeout=60*60)
    def get_regions(region_id):
        return Region.objects.get(pk=region_id)

    @staticmethod
    @Cached(cache="local")
    def get_user_regions(user_id):
        return [region_id for region_id, in UserRegion.objects.filter(user_id=user_id).values_list("region_id")]

    @staticmethod
    @Cached(cache="local")
    def get_item_list_by_region(module_id, region_id):
        module = Module.get_module(module_id)
        items = np.zeros((len(module.listed_items)), dtype=np.bool)
        for item_id, in ItemRegion.objects.filter(region_id=region_id).values_list("item_id"):
            items[module.items_index[Item.get_item_external_id_by_id(item_id)]] = True
        return items

    @staticmethod
    def load_to_cache():
        with click.progressbar(Region.objects.all(), label="Loading regions to cache") as bar:
            for region in bar:
                Region.get_regions.lock_this(
                    Region.get_regions.cache.set
                )(Region.get_regions.key % region.pk, region, Region.get_regions.timeout)
        users = {}
        with click.progressbar(UserRegion.objects.all().values_list("user_id", "region_id"),
                               label="Loading user regions to cache") as bar:
            for user_id, region_id in bar:
                try:
                    users[user_id].append(region_id)
                except KeyError:
                    users[user_id] = [region_id]
            for user, regions in users.items():
                Region.get_user_regions.lock_this(
                    Region.get_user_regions.cache.set
                )(Region.get_user_regions.key % user, regions, Region.get_user_regions.timeout)
        items = np.zeros((Region.objects.aggregate(max=models.Max("pk"))["max"],
                          Item.objects.aggregate(max=models.Max("pk"))["max"]))
        with click.progressbar(ItemRegion.objects.all().values_list("item_id", "region_id"),
                               label="Loading item regions to cache") as bar:
            for item_id, region_id in bar:
                items[region_id-1, item_id-1] = 1
        for i in range(items.shape[0]):
            Region.get_item_list_by_region.lock_this(
                Region.get_item_list_by_region.cache.set
            )(Region.get_item_list_by_region.key % (i+1), items[i, :], Region.get_item_list_by_region.timeout)


class UserRegion(models.Model):
    """
    User regions
    """

    user = models.ForeignKey(User, verbose_name=_("user"), related_name="regions")
    region = models.ForeignKey(Region, verbose_name=_("region"))

    class Meta:
        verbose_name = _("user region")
        verbose_name_plural = _("user regions")
        unique_together = ("user", "region")

    def __str__(self):
        return "%s for %s" % (self.region, self.user)

    def __unicode__(self):
        return u"%s for %s" % (self.region, self.user)


class ItemRegion(models.Model):
    """
    User regions
    """

    item = models.ForeignKey(Item, verbose_name=_("item"), related_name="regions")
    region = models.ForeignKey(Region, verbose_name=_("region"))

    class Meta:
        verbose_name = _("item region")
        verbose_name_plural = _("item regions")
        unique_together = ("item", "region")

    def __str__(self):
        return "%s for %s" % (self.region, self.item)

    def __unicode__(self):
        return u"%s for %s" % (self.region, self.item)

from django.contrib import admin
admin.site.register([Region, ItemRegion, UserRegion])