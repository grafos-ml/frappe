# -*- coding: utf-8 -*-
"""
Created on 11 February 2014

Models for the logging system

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
"""

__author__ = "joaonrb"

from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.contrib.admin import site
from django.db import models
from recommender.models import Item, User


class Record(models.Model):
    """
    Record
    """

    RECOMMEND = 0
    CLICK_RECOMMENDED = 1
    INSTALL = 2
    REMOVE = 3
    CLICK = 4
    TYPES = {
        RECOMMEND: _("recommend"),
        CLICK_RECOMMENDED: _("click recommended"),
        INSTALL: _("install"),
        REMOVE: _("remove"),
        CLICK: _("click")
    }

    user = models.ForeignKey(User, to_field="external_id", verbose_name=_("user"), null=True, default=None)
    item = models.ForeignKey(Item, to_field="external_id", verbose_name=_("item"))
    timestamp = models.DateTimeField(_("timestamp"), auto_now_add=True)
    value = models.FloatField(_("value"), null=True, default=None)
    type = models.SmallIntegerField(_("type"), choices=TYPES.items(), default=RECOMMEND)

    class Meta:
        verbose_name = _("recommendation log")
        verbose_name_plural = _("recommendation logs")
        ordering = ["-timestamp", "user"]

    def __unicode__(self):
        return _("%(date)s: user %(user)s as %(type)s item %(item)s") % {
            "date": self.timestamp,
            "user": str(self.user.external_id),
            "type": Record.TYPES[self.type],
            "item": str(self.item.external_id)
        }

    @staticmethod
    def click_recommended(user, item):
        """
        Puts a click log into database

        :param user: User external_id
        :param item: Item external_id
        """
        app = get_object_or_404(Item, external_id=item)
        Record.objects.create(user=get_object_or_404(User, external_id=user), item=app, type=Record.CLICK)
        return app.store_url

    @staticmethod
    def recommended(user, *recommended):
        """
        Log Recommended Apps

        :param user: User
        :param recommended: List of items ids
        """
        items = {item.pk: item for item in Item.objects.filter(pk__in=recommended)}
        logs = [Record(user=user, item=items[e_id], value=rank) for rank, e_id in enumerate(recommended, start=1)]
        Record.objects.bulk_create(logs)

site.register([Record])