#! -*- encoding: utf-8 -*-
"""
Models for predictors
"""

from __future__ import division, absolute_import, print_function
from django.db import models
from django.utils.translation import ugettext as _
from frappe.decorators import Cached
from frappe.models.base import User
from frappe.models.fields import PythonObjectField

__author__ = "joaonrb"


class UserFactors(models.Model):
    """
    Tensor for users
    """
    user = models.ForeignKey(User, verbose_name=_("user"), unique=True)
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