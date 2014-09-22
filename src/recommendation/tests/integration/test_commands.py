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
import recommendation
from datetime import date, timedelta, datetime
from pkg_resources import resource_filename
from django.test import TransactionTestCase
from recommendation.management.commands import fill
from recommendation.models import Item

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


class TestFill(TransactionTestCase):

    @classmethod
    def setup_class(cls, *args, **kwargs):
        tmp_path = tempfile.mkdtemp(suffix="_frappe_testing")
        if not os.path.exists(tmp_path):
            os.makedirs(tmp_path)
        urllib.urlretrieve(datetime.strftime(date.today() - timedelta(1), PRODUCTION_SERVER), tmp_path+"/app.tgz")
        tar = tarfile.open(tmp_path+"/app.tgz")
        tar.extractall(members=json_files(tar), path=tmp_path)
        tar.close()
        cls.tmp_dir = tmp_path

    @classmethod
    def teardown_class(cls, *args, **kwargs):
        try:
            shutil.rmtree(cls.tmp_dir)  # delete directory
        except OSError as exc:
            if exc.errno != errno.ENOENT:  # ENOENT - no such file or directory
                raise  # re-raise exception

    def test_fill_production_items(self):
        """
        [production.commands] Test fill items from production.
        """
        try:
            fill.main("items", self.tmp_dir+"/apps")
        except Exception as e:
            assert False, "Fill raises an error with production errors (%s)" % e

    def test_number_of_items_in_db(self):
        """
        [production.commands] Test number of items in db after fill production items.
        """
        fill.main("items", self.tmp_dir+"/apps")
        db_count, file_count = Item.objects.count(), count_files(self.tmp_dir+"/apps")
        assert db_count == file_count, "Number of items in db is not the same (%d != %d)" % (db_count, file_count)

    def test_fill_users(self):
        """
        [production.commands] Test fill users after production items.
        """
        try:
            fill.main("items", self.tmp_dir+"/apps")
            fill.main("users", resource_filename(recommendation.__name__, "/data/users/"))
        except Exception as e:
            assert False, "Fill raises an error with production errors (%s)" % e
