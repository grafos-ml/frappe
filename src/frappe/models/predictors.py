#! -*- encoding: utf-8 -*-
"""
Models for predictors
"""
__author__ = "joaonrb"

try:
    import cPickle as pickle
except ImportError:
    import pickle
import json
import zlib
import numpy as np
from six import string_types
from django.db import models
from frappe.models.base import User
from frappe.models.module import PythonObjectField
from django.utils.translation import ugettext as _
from django.utils.six import with_metaclass
from django.db.models.signals import pre_save
from django.dispatch import receiver
from frappe.decorators import Cached


class TensorArrayForUser(models.Model):
    """
    Tensor for users
    """
    user = models.ForeignKey(User)