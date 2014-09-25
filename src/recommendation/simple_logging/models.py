# -*- coding: utf-8 -*-
"""
Created on 29 August 2014

Models for the logging system

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
"""

__author__ = "joaonrb"

from django.conf import settings
from django.utils.translation import ugettext as _
from django.contrib.admin import site
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import get_cache
from recommendation.models import Item, User
from recommendation.decorators import Cached

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
    @Cached(lock_id=0)
    def get_logs_for(user_id):
        """
        Get the user ids
        """
        return list(LogEntry.objects.filter(user_id=user_id).order_by("-timestamp")[:LOGGER_MAX_LOGS])

    @staticmethod
    def load_to_cache():
        for user in User.objects.all():
            LogEntry.load_user(user)

    @staticmethod
    def load_user(user):
        """
        Load a single user to cache
        """
        get_cache("default").set(
            "get_logs_for_%d" % user.pk,
            list(LogEntry.objects.filter(user=user).order_by("-timestamp")[:LOGGER_MAX_LOGS]),
            None
        )

    @staticmethod
    def add_logs(user, logs):
        cache = get_cache("default")
        k = "get_logs_for_%d" % user.pk
        old_logs = LogEntry.get_logs_for(user.pk)
        logs = logs + old_logs
        cache.set(k, logs[:LOGGER_MAX_LOGS], None)


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