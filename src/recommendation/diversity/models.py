# -*- coding: utf-8 -*-
"""
Created March 4, 2014

Diversification models necessary to apply the diversification to a recommendation

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from django.utils.translation import ugettext as _
from django.db import models
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

from django.contrib import admin
admin.site.register([Genre])