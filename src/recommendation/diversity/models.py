# -*- coding: utf-8 -*-
"""
Created September 3, 2014

Diversification models necessary to apply the diversification to a recommendation

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from itertools import chain
from collections import Counter
from django.utils.translation import ugettext as _
from django.db import models
from django.core.cache import get_cache
from django.db.models import Count
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib import admin
from recommendation.models import Item, CacheManager, IterableCacheManager


class Genre(models.Model):
    """
    Types of genres
    """
    name = models.CharField(_("name"), max_length=255)

    genre_by_id = IterableCacheManager("divallgen")
    genres_count = IterableCacheManager("divcount")

    class Meta:
        verbose_name = _("genre")
        verbose_name_plural = _("genre")

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    @staticmethod
    def load_to_cache():
        """
        Load size of items per genre

        :return:
        """
        for genre in Genre.objects.all():
            Genre.genre_by_id[genre.pk] = genre
        for gpk, c in Genre.objects.all().annotate(count=Count("items")).values_list("pk", "count"):
            Genre.genres_count[gpk] = c


class ItemGenre(models.Model):
    """
    Genres of the item
    """
    type = models.ForeignKey(Genre, verbose_name=_("type"), related_name="items")
    item = models.ForeignKey(Item, verbose_name=_("item"), related_name="genres")

    genre_by_item = CacheManager("divit")

    class Meta:
        verbose_name = _("item genre")
        verbose_name_plural = _("item genres")

    def __str__(self):
        return _("%(item)s's %(genre)s") % {"genre": self.type.name, "item": self.item.external_id}

    def __unicode__(self):
        return _("%(item)s's %(genre)s") % {"genre": self.type.name, "item": self.item.external_id}

    @staticmethod
    def load_to_cache():
        """
        Load size of items per genre

        :return:
        """
        for item in Item.objects.all():
            ItemGenre.genre_by_item[item.pk] = set([])
        for item in ItemGenre.objects.all():
            ItemGenre.genre_by_item[item.item.pk] = ItemGenre.genre_by_item[item.item.pk].union((item.type.pk,))

    @staticmethod
    def load_item(item):
        """
        Load a single item to cache
        :return:
        """
        ItemGenre.genre_by_item[item.pk] = set([])
        for item in ItemGenre.objects.all():
            ItemGenre.genre_by_item[item.item.pk] = ItemGenre.genre_by_item[item.item.pk].union((item.type.pk,))

    @staticmethod
    def genre_in(item_list):
        return Counter(chain(*(ItemGenre.genre_by_item[item.pk] for item in item_list)))

    @staticmethod
    def count_all():
        return get_cache("models").get("diversity_genre_size")


@receiver(post_save, sender=Item)
def load_item_to_cache(sender, **kwargs):
    ItemGenre.load_item(kwargs["instance"])


@receiver(post_save, sender=Genre)
def load_genre_to_cache(sender, **kwargs):
    genre = kwargs["instance"]
    Genre.genre_by_id[genre.pk] = genre
    Genre.genres_count[genre.pk] = 0


@receiver(post_save, sender=ItemGenre)
def load_item_genre_to_cache(sender, **kwargs):
    item = kwargs["instance"]
    ItemGenre.genre_by_item[item.item.pk] = ItemGenre.genre_by_item[item.item.pk].union((item.type.pk,))
    Genre.genres_count[item.type.pk] += 1


admin.site.register([Genre, ItemGenre])