# -*- coding: utf-8 -*-
"""
Created on 29 August 2014

Models for the logging system

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
"""

__author__ = "joaonrb"

from collections import deque
from django.conf import settings
from django.utils.translation import ugettext as _
from django.contrib.admin import site
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from recommendation.models import Item, User, CacheManager

LOGGER_MAX_LOGS = 10 if settings.TESTING_MODE else getattr(settings, "LOGGER_MAX_LOGS", 50)


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

    user = models.ForeignKey(User, verbose_name=_("user"), null=True, default=None, db_constraint=False)
    item = models.ForeignKey(Item, verbose_name=_("item"), db_constraint=False)
    timestamp = models.DateTimeField(_("timestamp"), auto_now_add=True)
    value = models.FloatField(_("value"), null=True, default=None)
    type = models.SmallIntegerField(_("type"), choices=TYPES.items(), default=RECOMMEND)

    logs_for = CacheManager("slentries", "distributed")

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
            LogEntry.load_user(user)

    @staticmethod
    def load_user(user):
        """
        Load a single user to cache
        """
        logs = LogEntry.objects.filter(user=user).order_by("-timestamp")[:LOGGER_MAX_LOGS]
        LogEntry.logs_for[user.pk] = deque(reversed(logs), LOGGER_MAX_LOGS)


@receiver(post_save, sender=LogEntry)
def add_log_to_cache(sender, instance, created, raw, using, update_fields, *args, **kwargs):
    """
    Add log to cache upon creation
    """
    logs = LogEntry.logs_for.get(instance.user.pk, deque([], LOGGER_MAX_LOGS))
    logs.append(instance)
    LogEntry.logs_for[instance.user.pk] = logs


@receiver(post_delete, sender=User)
def delete_user_to_cache(sender, instance, using, **kwargs):
    """
    Add log to cache upon creation
    """
    del LogEntry.logs_for[instance.pk]

site.register([LogEntry])