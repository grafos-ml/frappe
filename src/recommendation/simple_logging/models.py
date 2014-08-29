# -*- coding: utf-8 -*-
"""
Created on 29 August 2014

Models for the logging system

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
"""

__author__ = "joaonrb"

from django.utils.translation import ugettext as _
from django.contrib.admin import site
from django.db import models
from recommendation.models import Item, User


class LogEntry(models.Model):
    """
    Log entry for the recommendation system
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

    user = models.ForeignKey(User, to_field="external_id", verbose_name=_("user"), null=True, default=None,
                             db_constraint=False)
    item = models.ForeignKey(Item, to_field="external_id", verbose_name=_("item"), db_constraint=False)
    timestamp = models.DateTimeField(_("timestamp"), auto_now_add=True)
    value = models.FloatField(_("value"), null=True, default=None)
    type = models.SmallIntegerField(_("type"), choices=TYPES.items(), default=RECOMMEND)

    class Meta:
        verbose_name = _("log entry")
        verbose_name_plural = _("log entries")
        ordering = ("-timestamp", "user")

    def __unicode__(self):
        return _("%(date)s: user %(user)s as %(type)s item %(item)s") % {
            "date": self.timestamp,
            "user": str(self.user.external_id),
            "type": LogEntry.TYPES[self.type],
            "item": str(self.item.external_id)
        }

    def __str__(self):
        return _("%(date)s: user %(user)s as %(type)s item %(item)s") % {
            "date": self.timestamp,
            "user": str(self.user.external_id),
            "type": LogEntry.TYPES[self.type],
            "item": str(self.item.external_id)
        }

site.register([Record])