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

from django.utils.translation import ugettext as _
from django.db import models
from ffos.models import FFOSApp, FFOSUser


class Log(models.Model):
    """
    
    """

    CLICK = 0
    INSTALL = 1
    REMOVE = 2
    TYPES = {
        CLICK: _("click"),
        INSTALL: _("install"),
        REMOVE: _("remove")
    }

    user = models.ForeignKey(FFOSUser, to_field="external_id",
                             verbose_name=_("user"))
    item = models.ForeignKey(FFOSApp, related_name="external_id",
                             verbose_name=_("item"))
    timestamp = models.DateTimeField(_("timestamp"), auto_now_add=True)
    value = models.DecimalField(_("value"), max_digits=6, decimal_places=4,
                                null=True, default=None)
    type = models.SmallIntegerField(_("type"), choices=TYPES.items(),
                                    default=CLICK)

    class Meta:
        verbose_name = _("log")
        verbose_name_plural = _("logs")
        order_with_respect_to = "user"
        ordering = ['-timestamp', 'user']

    def __unicode__(self):
        return _("%(date)s: user %(user)s as %(type)s item %(item)s") % {
            "date": self.timestamp,
            "user": str(self.user.external_id),
            "type": Log.TYPES[self.type],
            "item": str(self.item.external_id)
        }
