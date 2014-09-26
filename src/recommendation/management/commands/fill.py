#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Frappe fill - Fill database

Usage:
  fill (item|user) <path>
  fill (item|user) --webservice=<url>
  fill (item|user) (--mozilla-dev | --mozilla-prod) [today | yesterday | <date>]
  fill --help
  fill --version

Options:
  <path>                  Path to the user/item files. This path must have only users or items.
  -s --webservice=<url>   Get the files from a url as a tarball file.
  -m --mozilla-dev        Specific web service from mozilla FireFox OS App Store developing data.
  -M --mozilla-prod       Specific web service from mozilla FireFox OS App Store production data.
  today yesterday <date>  Specific date to query the mozilla data. Date format YYYY-MM-DD. [default: yesterday]
  -h --help               Show this screen.
  -v --version            Show version.
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
from datetime import date, timedelta, datetime
from django.db import connection
from django.db.models import Q
from django_docopt_command import DocOptCommand
from django.conf import settings
from recommendation.models import Item, User, Inventory
from recommendation.diversity.models import Genre, ItemGenre
from recommendation.language.models import Locale
from recommendation.default_settings import TESTING_MODE

MOZILLA_DEV_ITEMS_API = "https://marketplace-dev-cdn.allizom.org/dumped-apps/tarballs/%Y-%m-%d.tgz"
MOZILLA_PROD_ITEMS_API = "https://marketplace.cdn.mozilla.net/dumped-apps/tarballs/%Y-%m-%d.tgz"
BULK_QUERY = "INSERT INTO %(table)s %(columns)s VALUES %(values)s;"


class FillTool(object):

    TMP_FILE = "tmp.tgz"

    def __init__(self, parameters):
        self.parameters = parameters
        self.is_item = parameters["item"]
        self.is_user = parameters["user"]
        self.use_tmp = True
        self.path = self.tmp_dir = None
        if parameters["--version"]:
            print("Frappe fill 2.0")
            return
        if parameters["<path>"]:
            self.path = parameters["<path>"]
            self.use_tmp = False
        elif parameters["--webservice"]:
            self.tmp_dir = self.path = self.get_files(parameters["--webservice"])
        elif parameters["--mozilla-dev"] or parameters["--mozilla-prod"]:
            mozilla = MOZILLA_DEV_ITEMS_API if parameters["--mozilla-dev"] is not None else MOZILLA_PROD_ITEMS_API
            url = datetime.strftime(self.get_date(), mozilla)
            self.tmp_dir = self.path = self.get_files(url)
        self.objects = []

    def get_files(self, url):
        tmp_path = tempfile.mkdtemp(suffix="_frappe")
        tmp_file = "/".join([tmp_path, self.TMP_FILE])
        urllib.urlretrieve(url, tmp_file)
        tar = tarfile.open(tmp_file)
        tar.extractall(members=FillTool.json_files(tar), path=tmp_path)
        tar.close()
        return tmp_path

    @staticmethod
    def json_files(members):
        """
        Pull .json files only
        """
        for tarinfo in members:
            name = os.path.splitext(tarinfo.name)
            if name[1] == ".json" and name[0][0] != ".":
                yield tarinfo

    def get_date(self):
        """
        Return a date passed in the pararameters
        :return: A datetime
        """
        if self.parameters["<date>"]:
            return datetime.strptime(self.parameters["date>"], "%Y-%m.%d").date()
        if self.parameters["today"]:
            return date.today()
        # Return yesterday
        return date.today() - timedelta(1)

    def load(self):
        """
        Load the files to db
        """
        if self.path:
            try:
                self.load_files()
                logging.debug("Load files into memory")
                self.fill_db()
                logging.debug("Files loaded to database")
            finally:
                if self.use_tmp:
                    self.clean_tmp()
                    logging.debug("Tmp files deleted")
                logging.debug("Done!")

    def load_files(self):
        """
        Load files to memory
        """
        for path, _, files in os.walk(self.path):
            for name in files:
                if name[-5:].lower() == '.json':
                    f = '/'.join([path, name])
                    self.objects.append(json.load(open(f)))

    def fill_db(self):
        """
        Put objects in db
        """
        if self.is_item:
            self.fill_db_with_items()
        else:
            self.fill_db_with_users()

    def fill_db_with_items(self):
        """
        Put items in db
        """
        objs = []
        for obj in self.objects:
            if "app_type" in obj:
                obj["id"] = str(obj["id"])
                objs.append(obj)
        self.objects = objs
        json_items = {json_item["id"]: json_item for json_item in self.objects}  # Map items for easy treatment
        items = {item.external_id: item for item in Item.objects.filter(external_id__in=json_items.keys())}
        new_items = {}
        categories = set([])
        locales = set([])
        for item_eid, json_item in json_items.items():
            if item_eid not in items:
                try:
                    name = json_item[json_item["default_locale"]]
                except KeyError:
                    name = json_item["name"]
                new_items[item_eid] = Item(external_id=item_eid, name=name)
            json_categories = json_item.get("categories", None) or ()
            if isinstance(json_categories, basestring):
                categories.add(json_categories)
            else:
                categories = categories.union(json_item["categories"])

            json_locales = json_item.get("supported_locales", None) or ()
            if isinstance(json_locales, basestring):
                locales.add(json_locales)
            else:
                locales = locales.union(json_locales)
        logging.debug("Items ready to be saved")
        if connection.vendor == "sqlite":
            new_items_list = list(new_items.values())
            for i in range(0, len(new_items_list), 100):
                j = i+100
                Item.objects.bulk_create(new_items_list[i:j])
        else:
            Item.objects.bulk_create(new_items.values())
        logging.debug("New items saved with bulk_create")
        for item in Item.objects.filter(external_id__in=new_items.keys()):
            items[item.external_id] = item
        assert len(items) == len(self.objects), \
            "Size of items and size of self.objects are different (%d != %d)" % (len(items), len(self.objects))

        if "recommendation.diversity" in settings.INSTALLED_APPS and not TESTING_MODE:
            logging.debug("Preparing genres")
            db_categories = self.get_genres(categories)
            self.fill_item_genre(items, db_categories)
            logging.debug("Genres loaded")

        if "recommendation.language" in settings.INSTALLED_APPS and not TESTING_MODE:
            logging.debug("Preparing languages")
            db_locales = self.get_locales(locales)
            self.fill_item_locale(items, db_locales)
            logging.debug("Locales loaded")

    @staticmethod
    def get_genres(genres_names):
        """
        Get categories from database and create the ones that don't exist.
        :param genres_names:
        :return: A dict with Genres mapped to their name
        """
        genres = {genre.name: genre for genre in Genre.objects.filter(name__in=genres_names)}
        if len(genres) != len(genres_names):
            new_genres = {}
            for genre_name in genres_names:
                if genre_name not in genres:
                    new_genres[genre_name] = Genre(name=genre_name)

            if connection.vendor == "sqlite":
                new_genres_list = list(new_genres.values())
                for i in range(0, len(new_genres_list), 100):
                    j = i+100
                    Genre.objects.bulk_create(new_genres_list[i:j])
            else:
                Genre.objects.bulk_create(new_genres.values())
            for genre in Genre.objects.filter(name__in=new_genres):
                genres[genre.name] = genre
        return genres

    @staticmethod
    def get_locales(locales_names):
        """
        Get locales from database and create the ones that don't exist.
        :param locales_names:
        :return: A dict with Locales mapped to their name
        """
        query_locales = Q()
        json_locales = {}
        for locale in locales_names:
            try:
                language_code, country_code = locale.split("-")
            except ValueError:
                language_code, country_code = locale, ""
            json_locales[locale] = (language_code, country_code)
            query_locales = query_locales | Q(language_code=language_code, country_code=country_code)

        locales = {str(locale): locale for locale in Locale.objects.filter(query_locales)}
        if len(locales) != len(locales_names):
            new_locales = []
            new_query = Q()
            for json_locale in locales_names:
                if json_locale not in locales:
                    language_code, country_code = json_locales[json_locale]
                    new_locales.append(Locale(language_code=language_code, country_code=country_code))
                    new_query = new_query | Q(language_code=language_code, country_code=country_code)

            if connection.vendor == "sqlite":
                for i in range(0, len(new_locales), 100):
                    j = i+100
                    Locale.objects.bulk_create(new_locales[i:j])
            else:
                Locale.objects.bulk_create(new_locales)
            for locale in Locale.objects.filter(new_query):
                locales[str(locale)] = locale
        return locales

    def fill_item_genre(self, items, genres):
        """
        Fill item genres connection
        :param items:
        :param genres:
        :return:
        """
        item_genres = []
        for json_item in self.objects:
            json_genres = json_item.get("categories", None) or ()
            for json_genre in json_genres:
                item_genres.append(ItemGenre(item=items[json_item["id"]], type=genres[json_genre]))
        if connection.vendor == "sqlite":
            for i in range(0, len(item_genres), 100):
                j = i+100
                ItemGenre.objects.bulk_create(item_genres[i:j])
        else:
            ItemGenre.objects.bulk_create(item_genres)

    def fill_item_locale(self, items, locales):
        """
        Fill item locales connection
        :param items:
        :param locales:
        :return:
        """
        item_locale = []
        for json_item in self.objects:
            json_locales = json_item.get("supported_locales", None) or ()
            for locale in json_locales:
                item_locale.append("(%s, %s)" % (locales[locale].pk, items[json_item["id"]].pk))
        cursor = connection.cursor()
        if connection.vendor == "sqlite":
            for i in range(0, len(item_locale), 100):
                j = i+100
                cursor.execute(BULK_QUERY % {
                    "table": "language_locale_items",
                    "columns": "(locale_id, item_id)",
                    "values": ", ".join(item_locale[i:j])
                })
        else:
            cursor.execute(BULK_QUERY % {
                "table": "language_locale_items",
                "columns": "(locale_id, item_id)",
                "values": ", ".join(item_locale)
            })
        cursor.close()

    def clean_tmp(self):
        """
        Remove items from tmp path
        :return:
        """
        try:
            shutil.rmtree(self.tmp_dir)  # delete directory
        except OSError as exc:
            if exc.errno != errno.ENOENT:  # ENOENT - no such file or directory
                raise  # re-raise exception

    def fill_db_with_users(self):
        """
        Put users in db
        :return:
        """
        json_users = {json_user["user"]: json_user for json_user in self.objects}  # Map users for easy treatment
        users = User.objects.filter(external_id__in=json_users)
        new_users = {}
        items = set([])
        for user_eid, json_user in json_users.items():
            if user_eid not in users:
                new_users[user_eid] = User(external_id=user_eid)
            pass  # TODO
        User.objects.bulk_create(new_users.items())


class Command(DocOptCommand):
    docs = __doc__

    def handle_docopt(self, arguments):
        # arguments contains a dictionary with the options
        try:
            fill_command = FillTool(arguments)
            fill_command.load()
        except:
            traceback.print_exception(*sys.exc_info())
