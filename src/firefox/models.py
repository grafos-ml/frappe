# -*- coding: utf-8 -*-
"""
Created March 5, 2014

Models for FireFox recommendation system

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from django.utils.translation import ugettext as _
from django.db import models
from recommendation.models import Item


class Details(Item):
    """
    Some item Details for the FireFox apps to use th recommendation
    """
    description = models.TextField(_("description"), null=True, blank=True)
    url = models.URLField(_("urls"))
    slug = models.CharField(_("slug"), max_length=255)

    class Meta:
        verbose_name = _("detail")
        verbose_name_plural = _("details")

    @staticmethod
    def slug_to_item_place(slug):
        """
        Receives the item slug to retrieve the item place url.

        :param slug: Slug of the item
        :type slug: str
        :return: The item url place
        :rtype: str
        """
        return "https://marketplace.firefox.com/app/%s/" % slug

    def place_url(self):
        """
        Return this item url place
        """
        return self.slug_to_item_place(self.slug)