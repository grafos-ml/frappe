# -*- coding: utf-8 -*-
"""
Created March 4, 2014

Diversification models necessary to apply the diversification to a recommendation

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from django.utils.translation import ugettext as _
from django.db import models
from django.core.cache import get_cache
from django.db.models import Count
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib import admin
from recommendation.models import Item


class Genre(models.Model):
    """
    Genres of the item
    """

    name = models.CharField(_("name"), max_length=255)
    items = models.ManyToManyField(Item, verbose_name=_("items"), related_name="genres")

    class Meta:
        verbose_name = _("genre")
        verbose_name_plural = _("genres")

    def __str__(self):
        return self.name

    @staticmethod
    def load_to_cache():
        """
        Load size of items per genre

        genres = Genre.genre_in(recommendation)  # frequency in rec, frequency in DB

        :return:
        """
        cache = get_cache("models")
        cache.set("diversity_counts", dict(
            Genre.objects.all().annotate(count=Count("items")).values_list("name", "count")
        ), None)
        cache.set("diversity_genre_per_item", dict(
            Item.objects.all().values_list("id", "genres__name")
        ), None)
        cache.set("diversity_genre_size", Genre.objects.all().count(), None)

    @staticmethod
    def genre_in(item_list):
        cache = get_cache("models")
        d_counts = cache.get("diversity_counts")
        items = cache.get("diversity_genre_per_item")
        result = {}
        for genres in (items[item] for item in item_list):
            if genres != None:
                for genre in ([genres] if isinstance(genres, (str, unicode)) else genres):
                    try:
                        result[genre] = result[genre][0]+1, result[genre][1]
                    except KeyError:
                        result[genre] = 1, d_counts[genre]
        return result.values()
    #colocar items => genres na cache

    @staticmethod
    def count_all():
        return get_cache("models").get("diversity_genre_size")


@receiver(post_save, sender=Item)
def reload_genres_cache(sender, **kwargs):
    Genre.load_to_cache()


admin.site.register([Genre])