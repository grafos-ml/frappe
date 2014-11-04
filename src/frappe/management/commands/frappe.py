#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Frappe
Create initial settings, fill data, train models, set caches and database-

Usage:
  frappe init [options...] <path>
  frappe --help
  frappe --version

Options:
  -i --initialize                  Initialize frappe database and initial data.
  -h --help                        Show this screen.
  --version                        Show version.
"""
__author__ = "joaonrb"

import os
import sys
import traceback
import logging
import tempfile
import urllib
import tarfile
import json
import errno
import shutil
import click
import itertools
from datetime import date, timedelta, datetime
from django.db.models import Q
from django_docopt_command import DocOptCommand
from django.conf import settings
from frappe.models import Item, User, Inventory

# TODO