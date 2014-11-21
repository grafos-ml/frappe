# -*- coding: utf-8 -*-
"""
Created on 29 August 2014

Models for the logging system

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
"""

__author__ = "joaonrb"

import os
from django.conf import settings
from django.utils.translation import ugettext as _
from django.contrib.admin import site
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import get_cache
from frappe.models import Item, User
from frappe.decorators import Cached

LOGGER_MAX_LOGS = 10 if int(os.environ.get("FRAPPE_TEST", 0)) else getattr(settings, "LOGGER_MAX_LOGS", 50)


class LogEntry(models.Model):
    """
    Log entry for the recommendation system
    """
    points = (
        lambda x: -(x/2.),         # LogEntry.RECOMMEND
        lambda x: 0,               # LogEntry.INSTALL
        lambda x: -10,             # LogEntry.REMOVE
        lambda x: 3,               # LogEntry.CLICK
    )

    RECOMMEND = 0
    ACQUIRE = 1
    DROP = 2
    CLICK = 3
    TYPES = {
        RECOMMEND: _("recommend"),
        ACQUIRE: _("install"),
        DROP: _("remove"),
        CLICK: _("click")
    }

    user = models.ForeignKey(User, verbose_name=_("user"), null=True, default=None, db_constraint=False,
                             to_field="external_id")
    item = models.ForeignKey(Item, verbose_name=_("item"), db_constraint=False, to_field="external_id")
    source = models.CharField(_("source"), max_length=50)
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
            "user": str(self.user_id),
            "type": LogEntry.TYPES[self.type],
            "item": str(self.item_id)
        }

    def __str__(self):
        return _("%(date)s: user %(user)s as %(type)s item %(item)s") % {
            "date": self.timestamp,
            "user": str(self.user_id),
            "type": LogEntry.TYPES[self.type],
            "item": str(self.item_id)
        }

    @staticmethod
    @Cached(lock_id=0)
    def get_logs_for(user_eid):
        """
        Get the user ids
        """
        result = {}
        for log in LogEntry.objects.filter(user_id=user_eid).order_by("-timestamp")[:LOGGER_MAX_LOGS]:
            result[log.item_id] = result.get(log.item_id, 0) + LogEntry.points[log.type](log.value)
        return result

    @staticmethod
    def load_to_cache():
        for user in User.objects.all():
            LogEntry.load_user(user)

    @staticmethod
    def load_user(user):
        """
        Load a single user to cache
        """
        LogEntry.get_logs_for.lock_this(
            LogEntry.get_logs_for.cache.set
        )(LogEntry.get_logs_for.key % user.pk,
          list(LogEntry.objects.filter(user=user).order_by("-timestamp")[:LOGGER_MAX_LOGS]),
          LogEntry.get_logs_for.timeout)

    @staticmethod
    def add_logs(user, logs):
        old_logs = LogEntry.get_logs_for()
        for log in logs:
            old_logs[log.item_id] = old_logs.get(log.item_id, 0) + LogEntry.points[log.type](log.value)
        LogEntry.get_logs_for.lock_this(
            LogEntry.get_logs_for.cache.set
        )(LogEntry.get_logs_for.key(user.external_id), old_logs, LogEntry.get_logs_for.timeout)


@receiver(post_save, sender=LogEntry)
@LogEntry.get_logs_for.lock_this
def add_log_to_cache(sender, instance, created, raw, using, update_fields, *args, **kwargs):
    """
    Add log to cache upon creation
    """
    LogEntry.add_logs(instance.user, [instance])


@receiver(post_delete, sender=User)
@LogEntry.get_logs_for.lock_this
def delete_user_to_cache(sender, instance, using, **kwargs):
    """
    Add log to cache upon creation
    """
    get_cache("default").delete("get_logs_for_%d" % instance.pk)

site.register([LogEntry])