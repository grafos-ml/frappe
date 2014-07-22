# -*- coding: utf-8 -*-
"""
Created on 18 July 2014

Models for ab testing

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
"""

from django.utils.translation import ugettext as _
from django.contrib import admin
from django.db import models
from recommendation.models import User
from recommendation.records.models import Record
from recommendation.decorators import PutInThreadQueue


class ABEvent(Record):
    """
    Model to associate recommendation.record with ab test records
    """
    model = models.CharField(_("model"), max_length=255, null=True, blank=True)
    model_identifier = models.SmallIntegerField("model id", null=True, blank=True)

    class Meta:
        verbose_name = _("ab testing event")
        verbose_name_plural = _("ab testing events")

    @staticmethod
    @PutInThreadQueue()
    def recommended(user, model_id, model, *recommended):
        """
        Log Recommended Apps

        :param user: User
        :param recommended: List of items ids
        """
        if isinstance(user, User):
            user = user.external_id
        for rank, e_id in enumerate(recommended, start=1):
            ABEvent(user_id=user, item_id=e_id, value=rank, model=model.get_name(), model_identifier=model_id).save()
        #logs = [ABEvent(user_id=user, item_id=e_id, value=rank) for rank, e_id in enumerate(recommended, start=1)]
        #ABEvent.objects.bulk_create(logs)
        #post_save.send(sender=Record, instance=logs)

admin.site.register([ABEvent])