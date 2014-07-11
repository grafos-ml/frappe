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
from recommendation.models import Item, User
from django.db.models import Count
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib import admin


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
        :return:
        """
        cache = get_cache("default")
        cache.set("diversity_counts", dict(
            Genre.objects.all().annotate(count=Count("items")).values_list("name", "count")), None)

    def get_count(self, name):
        cache = get_cache("default")
        return cache.get("diversity_counts")[name]
    #colocar items => genres na cache

@receiver(post_save, sender=Item)
def reload_genres_cache(sender, **kwargs):
    Genre.load_to_cache()


admin.site.register([Genre])