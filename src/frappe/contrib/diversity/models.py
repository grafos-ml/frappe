#! -*- coding: utf-8 -*-
"""
Created September 3, 2014

Diversification models necessary to apply the diversification to a recommendation

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""

from __future__ import division, absolute_import, print_function
import click
from itertools import chain
from collections import Counter
from django.utils.translation import ugettext as _
from django.db import models
from django.db.models import Count
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib import admin
from frappe.models import Item
from frappe.decorators import Cached

__author__ = "joaonrb"


class Genre(models.Model):
    """
    Types of genres
    """
    name = models.CharField(_("name"), max_length=255)

    class Meta:
        verbose_name = _("genre")
        verbose_name_plural = _("genre")

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    @staticmethod
    @Cached(timeout=60*60)
    def get_genre_by_id(genre_id):
        """
        Return the genre belonging to that id with and extra attribute: count_items
        :param genre_id:
        :return:
        """
        return Genre.objects.filter(pk=genre_id).annotate(count_items=Count("items"))[0]

    @staticmethod
    @Cached(timeout=60*60)
    def get_all_genres():
        """
        Get all genres
        :return:
        """
        return [genre_id for genre_id, in Genre.objects.all().values_list("pk")]

    @staticmethod
    def load_to_cache():
        """
        Load size of items per genre

        :return:
        """
        cache = Genre.get_genre_by_id.cache
        with click.progressbar(Genre.objects.all().annotate(count_items=Count("items")),
                               label="Loading genres to cache") as bar:
            for genre in bar:
                Genre.get_genre_by_id.lock_this(
                    cache.set
                )(Genre.get_genre_by_id.key(genre.pk), genre, Genre.get_genre_by_id.timeout)

        Genre.get_all_genres()


class ItemGenre(models.Model):
    """
    Genres of the item
    """
    type = models.ForeignKey(Genre, verbose_name=_("type"), related_name="items")
    item = models.ForeignKey(Item, verbose_name=_("item"), related_name="genres", to_field="external_id")

    class Meta:
        verbose_name = _("item genre")
        verbose_name_plural = _("item genres")
        unique_together = ("type", "item")

    def __str__(self):
        return _("%(item)s's %(genre)s") % {"genre": self.type.name, "item": self.item_id}

    def __unicode__(self):
        return _("%(item)s's %(genre)s") % {"genre": self.type.name, "item": self.item_id}

    @staticmethod
    @Cached()
    def get_genre_by_item(item_eid):
        """
        Get genres list for a specific item
        :param item_id:
        :return:
        """
        return [item_genre.type.pk for item_genre in ItemGenre.objects.filter(item_id=item_eid)]

    @staticmethod
    def load_to_cache():
        """
        Load size of items per genre

        :return:
        """
        genres = {}
        with click.progressbar(ItemGenre.objects.all(), label="Loading item by genres to cache") as bar:
            for item_genre in bar:
                try:
                    genres[item_genre.item_id].append(item_genre.type_id)
                except KeyError:
                    genres[item_genre.item_id] = [item_genre.type_id]
        cache = ItemGenre.get_genre_by_item.cache
        with click.progressbar(genres.items(), label="Loading genres by item to cache") as bar:
            for item_eid, genre in bar:
                ItemGenre.get_genre_by_item.lock_this(
                    cache.set
                )(ItemGenre.get_genre_by_item.key(item_eid), genre, ItemGenre.get_genre_by_item.timeout)

    @staticmethod
    def load_item(item):
        """
        Load a single item to cache
        :return:
        """
        ItemGenre.get_genre_by_item(item_id=item.pk)

    @staticmethod
    def genre_in(item_list):
        return Counter(chain(*(ItemGenre.get_genre_by_item(item_eid) for item_eid in item_list)))


@receiver(post_save, sender=Item)
def load_item_to_cache(sender, **kwargs):
    ItemGenre.get_genre_by_item(kwargs["instance"].external_id)

admin.site.register([Genre, ItemGenre])