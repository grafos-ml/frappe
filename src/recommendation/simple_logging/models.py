# -*- coding: utf-8 -*-
"""
Created on 29 August 2014

Models for the logging system

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
"""

__author__ = "joaonrb"

from collections import deque
from django.utils.translation import ugettext as _
from django.contrib.admin import site
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from recommendation.models import Item, User, CacheManager

MAX_LOGS_IN_CACHE = 1000

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

    entries = CacheManager("slentries")

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

    @staticmethod
    def load_to_cache():
        for user in User.objects.all():
            LogEntry.entries[user.pk] = \
                deque(LogEntry.objects.filter(user=user).order_by("timestamp")[0-MAX_LOGS_IN_CACHE:], MAX_LOGS_IN_CACHE)


@receiver(post_save, sender=LogEntry)
def add_log_to_cache(sender, instance, created, raw, using, update_fields, *args, **kwargs):
    """
    Add log to cache upon creation
    """
    logs = LogEntry.entries.get(instance.user.pk, deque([], MAX_LOGS_IN_CACHE))
    logs.append(instance)
    LogEntry.entries[instance.user.pk] = logs
    Item.item_by_id[instance.pk] = instance
    Item.item_by_external_id[instance.external_id] = instance


@receiver(post_delete, sender=User)
def delete_user_to_cache(sender, instance, using, **kwargs):
    """
    Add log to cache upon creation
    """
    del LogEntry.entries[instance.pk]

site.register([LogEntry])