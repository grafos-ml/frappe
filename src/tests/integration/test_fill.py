#! -*- encoding: utf-8 -*-
"""
Test package for recommendation django commands in production environment.
"""
__author__ = "joaonrb"

import os
import errno
import shutil
import urllib
import tarfile
import tempfile
from datetime import date, timedelta, datetime
from pkg_resources import resource_filename
from django.db import connection
from django.test import TestCase
from django.core.cache import get_cache
import frappe
from frappe.management.commands import fill
from frappe.models import Item, User, Inventory
from frappe.contrib.region.models import Region, ItemRegion, UserRegion
from frappe.contrib.diversity.models import ItemGenre, Genre


PRODUCTION_SERVER = 'https://marketplace.cdn.mozilla.net/dumped-apps/tarballs/%Y-%m-%d.tgz'


def json_files(members):
    """
    Pull .json files only
    """
    for tarinfo in members:
        name = os.path.splitext(tarinfo.name)
        if name[1] == ".json" and name[0][0] != ".":
            yield tarinfo


def count_files(path):
    count = 0
    for root, dirs, files in os.walk(path):
        count += len(files) + sum(count_files(d) for d in dirs)
    return count


class TestFill(TestCase):

    @classmethod
    def teardown(cls, *args, **kwargs):
        ItemRegion.objects.all().delete()
        UserRegion.objects.all().delete()
        Region.objects.all().delete()
        ItemGenre.objects.all().delete()
        Genre.objects.all().delete()
        # This for sqlite delete
        if connection.vendor == "sqlite":
            while Inventory.objects.all().count() != 0:
                Inventory.objects.filter(pk__in=Inventory.objects.all()[:100]).delete()
            while Item.objects.all().count() != 0:
                Item.objects.filter(pk__in=Item.objects.all()[:100]).delete()
        else:
            Inventory.objects.all().delete()
            Item.objects.all().delete()
        User.objects.all().delete()
        get_cache("default").clear()
        get_cache("owned_items").clear()
        get_cache("module").clear()

    def test_fill_production_items(self):
        """
        [production.commands] Test fill items from production.
        """
        try:
            fill.FillTool({"items": True, "--mozilla": True, "prod": True}).load()
        except Exception as e:
            assert False, "Fill raises an error with production errors (%s)" % e

    def test_number_of_items_in_db(self):
        """
        [production.commands] Test number of items in db after fill production items.
        """
        tmp_path = tempfile.mkdtemp(suffix="_frappe_testing")
        if not os.path.exists(tmp_path):
            os.makedirs(tmp_path)
        urllib.urlretrieve(datetime.strftime(date.today() - timedelta(1), PRODUCTION_SERVER), tmp_path+"/app.tgz")
        tar = tarfile.open(tmp_path+"/app.tgz")
        tar.extractall(members=json_files(tar), path=tmp_path)
        tar.close()

        fill.FillTool({"items": True, "--mozilla": True, "prod": True}).load()
        db_count, file_count = Item.objects.count(), count_files(tmp_path+"/apps")
        assert db_count == file_count, "Number of items in db is not the same (%d != %d)" % (db_count, file_count)

        try:
            shutil.rmtree(tmp_path)  # delete directory
        except OSError as exc:
            if exc.errno != errno.ENOENT:  # ENOENT - no such file or directory
                raise  # re-raise exception

    def test_fill_users(self):
        """
        [production.commands] Test fill users after production items.
        """
        try:
            path = resource_filename(recommendation.__name__, "/")
            fill.FillTool({"items": True, "--mozilla": True, "prod": True}).load()
            fill.FillTool({"users": True, "--mozilla": True, "<path>": path+"data/user"}).load()
        except Exception as e:
            assert False, "Fill raises an error with production errors (%s)" % e