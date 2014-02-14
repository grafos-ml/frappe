# -*- coding: utf-8 -*-
"""
Created on 11 February 2014

Models for the logging system

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
"""

__author__ = {
    'name': 'joaonrb',
    'e-mail': 'joaonrb@gmail.com'
}

from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.contrib.admin import site
from django.db import models
from ffos.models import FFOSApp, FFOSUser


class RLog(models.Model):
    """
    
    """

    RECOMMEND = 0
    CLICK = 1
    INSTALL = 2
    REMOVE = 3
    TYPES = {
        RECOMMEND: _("recommend"),
        CLICK: _("click"),
        INSTALL: _("install"),
        REMOVE: _("remove")
    }

    user = models.ForeignKey(FFOSUser, to_field="external_id", verbose_name=_("user"))
    item = models.ForeignKey(FFOSApp, to_field="external_id", verbose_name=_("item"))
    timestamp = models.DateTimeField(_("timestamp"), auto_now_add=True)
    value = models.DecimalField(_("value"), max_digits=6, decimal_places=4, null=True, default=None)
    type = models.SmallIntegerField(_("type"), choices=TYPES.items(), default=RECOMMEND)

    class Meta:
        verbose_name = _("recommendation log")
        verbose_name_plural = _("recommendation logs")
        #order_with_respect_to = "user"
        ordering = ["-timestamp", "user"]

    def __unicode__(self):
        return _("%(date)s: user %(user)s as %(type)s item %(item)s") % {
            "date": self.timestamp,
            "user": str(self.user.external_id),
            "type": RLog.TYPES[self.type],
            "item": str(self.item.external_id)
        }

    @staticmethod
    def click(user, app):
        """
        Puts a click log into database
        """
        app = get_object_or_404(FFOSApp, external_id=app)
        RLog.objects.create(user=get_object_or_404(FFOSUser, external_id=user), item=app, type=RLog.CLICK)
        return app.store_url

    @staticmethod
    def recommended(user, *recommended):
        """
        Log Recommended Apps

        .. user
        """
        apps = {app.pk: app for app in FFOSApp.objects.filter(pk__in=recommended)}
        logs = [RLog(user=user, item=apps[e_id], value=rank) for rank, e_id in enumerate(recommended, start=1)]
        RLog.objects.bulk_create(logs)

site.register([RLog])