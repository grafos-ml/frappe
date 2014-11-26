# -*- coding: utf-8 -*-
"""
frappe - settings.unit
joaonrb, 26 November 2014

Unit test settings
"""

from __future__ import division, absolute_import, print_function
from settings.base import *

__author__ = "joaonrb"


DATABASES = {
    "default": databases.UNIT
}

CACHES["owned_items"] = caches.LOCAL