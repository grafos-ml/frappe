# -*- encoding=utf-8 -*-
"""
The region models module.
"""
__author__ = "joaonrb"


import click
from django.db import models
from django.utils.translation import ugettext as _
from recommendation.models import Item, User
from recommendation.decorators import Cached


