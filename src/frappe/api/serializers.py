# -*- coding: utf-8 -*-
"""
frappe - frappe.api
joaonrb, 01 December 2014

Documentation TODO
"""

from __future__ import division, absolute_import, print_function
from rest_framework import serializers

__author__ = "joaonrb"


class UserSerializer(serializers.Serializer):
    external_id = serializers.CharField(max_length=255)