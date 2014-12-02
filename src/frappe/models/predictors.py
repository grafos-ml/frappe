#! -*- encoding: utf-8 -*-
"""
Models for predictors
"""

from __future__ import division, absolute_import, print_function
from django.db import models
from django.utils.translation import ugettext as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from frappe.decorators import Cached
from frappe.models.base import User, Inventory
from frappe.models.fields import PythonObjectField

__author__ = "joaonrb"


class UserFactors(models.Model):
    """
    Tensor for users
    """
    user = models.ForeignKey(User, verbose_name=_("user"), unique=True, to_field="external_id")
    array = PythonObjectField(_("array"), blank=True)

    class Meta:
        verbose_name = _("user factors")
        verbose_name_plural = _("user factors")

    def __str__(self):
        return self.array

    def __unicode__(self):
        return self.array

    @staticmethod
    @Cached()
    def get_user_factors(user_id):
        """
        Return user factor array
        :param user_id:
        :return:
        """
        return UserFactors.objects.get(user_id=user_id)


@receiver(post_save, sender=Inventory)
def add_reset_user_factors(sender, instance, created, raw, using, update_fields, *args, **kwargs):
    """
    Reset user factors when
    """
    UserFactors.objects.filter(user_id=instance.user_id).delete()
    UserFactors.get_user_factors.set((instance.user_id,), None)