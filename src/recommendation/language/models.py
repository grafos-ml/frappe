# -*- encoding=utf-8 -*-
"""
The locale models moudle. It must contain the locale
"""
__author__ = "joaonrb"


import click
from django.db import models
from django.utils.translation import ugettext as _
import numpy as np
from recommendation.models import Item, User
from recommendation.decorators import Cached


class Locale(models.Model):
    """
    Model for a specific locale
    """
    language_code = models.CharField(_("language code"), max_length=2)
    country_code = models.CharField(_("country code"), max_length=2, default="")
    name = models.CharField(_("country"), max_length=255, default="")
    items = models.ManyToManyField(Item, verbose_name=_("items"), through="ItemLocale", blank=True, null=True)
    users = models.ManyToManyField(User, verbose_name=_("users"), through="UserLocale", blank=True, null=True)

    class Meta:
        verbose_name = _("locale")
        verbose_name_plural = _("locales")
        unique_together = ("language_code", "country_code")

    def __str__(self):
        return "%s%s" % (self.language_code, "-%s" % self.country_code if self.country_code else "")

    def __unicode__(self):
        return u"%s%s" % (self.language_code, "-%s" % self.country_code if self.country_code else "")

    @staticmethod
    @Cached(cache="local", timeout=60*60)
    def get_all_locales():
        return {locale.pk: locale for locale in Locale.objects.all()}

    @staticmethod
    @Cached(cache="local")
    def get_item_locales(item_id):
        return set([pk[0] for pk in Item.get_item_by_id(item_id).locales.all().values_list("locale_id")])

    @staticmethod
    @Cached(cache="local")
    def get_user_locales(user_id):
        return set([pk[0] for pk in User.get_user_by_id(user_id).locales.all().values_list("locale_id")])

    @staticmethod
    @Cached(cache="local", timeout=60*60)
    def get_items_by_locale(locale_id):
        return set([pk[0] for pk in ItemLocale.objects.filter(locale_id=locale_id).values_list("item_id")])

    def save(self, *args, **kwargs):
        """
        Makes the codes to be saved always using lower case
        :param args:
        :param kwargs:
        :return:
        """
        self.language_code = self.language_code.lower()
        self.country_code = self.country_code.lower()
        super(Locale, self).save(*args, **kwargs)

    @staticmethod
    def load_to_cache():
        with click.progressbar(Locale.get_all_locales(), label="Loading locales to cache") as bar:
            for locale_id in bar:
                Locale.get_items_by_locale(locale_id)

        users = {}
        with click.progressbar(UserLocale.objects.all().values_list("user_id", "locale_id"),
                               label="Loading user locales to cache") as bar:
            for user_id, genre_id in bar:
                try:
                    users[user_id].add(genre_id)
                except KeyError:
                    users[user_id] = set([genre_id])
            for user_id, genres in users.items():
                Locale.get_user_locales.lock_this(
                    Locale.get_user_locales.cache.set
                )(Locale.get_user_locales.key % user_id, genres, Locale.get_user_locales.timeout)

        items = {}
        with click.progressbar(ItemLocale.objects.all().values_list("item_id", "locale_id"),
                               label="Loading item locales to cache") as bar:
            for item_id, genre_id in bar:
                try:
                    items[item_id].add(genre_id)
                except KeyError:
                    items[item_id] = set([genre_id])
            for item_id, genres in items.items():
                Locale.get_item_locales.lock_this(
                    Locale.get_item_locales.cache.set
                )(Locale.get_item_locales.key % item_id, genres, Locale.get_item_locales.timeout)


class ItemLocale(models.Model):
    """
    Many to many table to locales
    """

    locale = models.ForeignKey(Locale, verbose_name=_("locale"))
    item = models.ForeignKey(Item, verbose_name=_("item"), related_name="locales")

    class Meta:
        verbose_name = _("item locale")
        verbose_name_plural = _("item locales")
        unique_together = ("locale", "item")

    def __str__(self):
        return "%s: %s" % (self.item, self.locale)

    def __unicode__(self):
        return u"%s: %s" % (self.item, self.locale)


class UserLocale(models.Model):
    """
    Many to many table to locales
    """

    locale = models.ForeignKey(Locale, verbose_name=_("locale"))
    user = models.ForeignKey(User, verbose_name=_("user"), related_name="locales")

    class Meta:
        verbose_name = _("user locale")
        verbose_name_plural = _("user locales")
        unique_together = ("locale", "user")

    def __str__(self):
        return "%s: %s" % (self.user, self.locale)

    def __unicode__(self):
        return u"%s: %s" % (self.user, self.locale)


class Region(models.Model):
    """
    Models for region
    """

    name = models.CharField(_("name"), max_length=255, unique=True)

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
        return Region.objects.filter(pk=region_id)

    @staticmethod
    @Cached(cache="local")
    def get_user_regions(user_id):
        return UserRegion.objects.filter(user_id=user_id).value_list()

    @staticmethod
    @Cached(cache="local")
    def get_item_list_by_region(region_id):
        items = np.zeros((Item.objects.aggregate(max=models.Max("pk"))["max"]))
        for item in ItemRegion.objects.filter(region_id=region_id).values_list("item_id"):
            items[item-1] = 1
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

    user = models.ForeignKey(User, _("user"), related_name="regions")
    region = models.ForeignKey(Region, _("region"), related_name="users")

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

    item = models.ForeignKey(Item, _("item"), related_name="regions")
    region = models.ForeignKey(Region, _("region"), related_name="items")

    class Meta:
        verbose_name = _("item region")
        verbose_name_plural = _("item regions")
        unique_together = ("item", "region")

    def __str__(self):
        return "%s for %s" % (self.region, self.user)

    def __unicode__(self):
        return u"%s for %s" % (self.region, self.user)

from django.contrib import admin
admin.site.register([Locale, ItemLocale, UserLocale, Region, ItemRegion, UserRegion])