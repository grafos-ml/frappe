#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Frappe fill - Fill database

Usage:
  manage.py fill (item|user) <path>
  manage.py fill (item|user) --webservice=<url>
  manage.py fill (item|user) (--mozilla-dev | --mozilla-prod) [today | yesterday | <date>]
  manage.py fill --help
  manage.py fill --version

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

import logging
import os
import tempfile
import urllib
import tarfile
import json
from datetime import date, timedelta, datetime
from docopt import docopt
from django.db import connection
from django.db.models import Q
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from recommendation.models import Item
from recommendation.diversity.models import Genre, ItemGenre
from recommendation.language.models import Locale
from recommendation.default_settings import TESTING_MODE

MOZILLA_DEV_ITEMS_API = "https://marketplace-dev-cdn.allizom.org/dumped-apps/tarballs/%Y-%m-%d.tgz"
MOZILLA_PROD_ITEMS_API = "https://marketplace.cdn.mozilla.net/dumped-apps/tarballs/%Y-%m-%d.tgz"


class FillTool(object):

    TMP_FILE = "tmp.tgz"

    def __init__(self):
        self.parameters = docopt(__doc__, version="Frappe fill 2.0")
        self.is_item = self.parameters["item"]
        self.is_user = self.parameters["user"]
        self.use_tmp = True
        self.tmp_dir = None
        if self.parameters["<path>"]:
            self.path = self.parameters["<path>"]
            self.use_tmp = False
        elif self.parameters["--webservice"]:
            self.tmp_dir = self.path = self.get_files(self.parameters["--webservice"])
        else:
            url = datetime.strftime(self.get_date(),
                                    (self.parameters["--mozilla-dev"] or self.parameters["--mozilla-prod"]))
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
        return date.today() - timedelta(1)

    def load(self):
        """
        Load the files to db
        """
        self.load_files()
        logging.debug("Load files into memory")
        self.fill_db()
        logging.debug("Files loaded to database")
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
        Item.objects.bulk_create(new_items.values())
        logging.debug("New items saved with bulk_create")
        for item in Item.objects.filter(external_id__in=new_items.keys()):
            items[item.external_id] = item
        assert len(items) == self.objects, "Size of items and size of self.objects are different"

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
        genres = {genre.name: genre for genre in Genre.objects.filter(names__in=genres_names)}
        if len(genres) != len(genres_names):
            new_genres = {}
            for genre_name in genres_names:
                if genre_name not in genres:
                    new_genres[genre_name] = Genre(name=genre_name)
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

            Locale.objects.bulk_create(new_locales)
            for locale in Locale.objects.filter(new_query):
                locales[str(locale)] = locale
        return locales





