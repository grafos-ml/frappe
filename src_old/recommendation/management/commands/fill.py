#!/usr/bin/env python
#! -*- coding: utf-8 -*-
"""
Frappe fill - Fill database

Usage:
  fill (items|users) <path> [options ...] [--verbose]
  fill (items|users) --webservice=<url> [options ...] [--verbose]
  fill items --mozilla (dev | prod) [today | yesterday | <date>] [--verbose]
  fill (items|users) --mozilla <path> [--verbose]
  fill --help
  fill --version

Options:
  -i --item=<field>                Item identifier in file [default: external_id].
  -u --user=<field>                User identifier in file [default: external_id].
  --item-file-identifier=<field>   Field that identify item json file [default: item].
  --user-file-identifier=<field>   File that identify user json file [default: user].
  --item-genres=<field>            Field in items for genres [default: genres].
  --item-locales=<field>           Field in items for locales [default: locales].
  --user-items=<field>             Field in user for user items [default: items].
  --user-item-identifier=<field>   Field to identify item in user inventory [default: external_id].
  --user-item-acquired=<field>     Field to identify item acquisition date [default: acquired].
  --user-item-dropped=<field>      Field to identify item acquisition date [default: dropped].
  --date-format=<field>            Field to date format [default: %Y-%m-%dT%H:%M:%S]
  -v --verbose                     Set verbose mode.
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
from recommendation.models import Item, User, Inventory
from recommendation.diversity.models import Genre, ItemGenre
from recommendation.language.models import Locale, ItemLocale, Region, ItemRegion, UserRegion, UserLocale


MOZILLA_DEV_ITEMS_API = "https://marketplace-dev-cdn.allizom.org/dumped-apps/tarballs/%Y-%m-%d.tgz"
MOZILLA_PROD_ITEMS_API = "https://marketplace.cdn.mozilla.net/dumped-apps/tarballs/%Y-%m-%d.tgz"

MOZILLA_ITEM_FILE_IDENTIFIER = "app_type"
MOZILLA_ITEM_FIELD = "id"
MOZILLA_ITEM_LOCALES_FIELD = "supported_locales"
MOZILLA_ITEM_GENRES_FIELD = "categories"
MOZILLA_USER_FILE_IDENTIFIER = "user"
MOZILLA_USER_FIELD = "user"
MOZILLA_USER_ITEMS = "installed_apps"
MOZILLA_USER_ITEM_IDENTIFIER = "id"
MOZILLA_USER_ITEM_ACQUISITION_FIELD = "installed"
MOZILLA_USER_ITEM_DROPPED_FIELD = "dropped"
MOZILLA_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

SQLITE_MAX_ROWS = 950
MAX_FILES_TO_MEM = 100  # if connection.vendor != "sqlite" else 10


class FillTool(object):

    TMP_FILE = "tmp.tgz"

    def __init__(self, parameters):
        self.parameters = parameters
        self.is_item = parameters.get("items", False)
        self.is_user = parameters.get("users", False)
        self.use_tmp = True
        self.path = self.tmp_dir = None
        self. path = self.tmp_dir = None
        if parameters.get("--version", False):
            print("Frappe fill 2.0")
            return
        if parameters.get("--webservice", False):
            self.tmp_dir = self.path = self.get_files(parameters["--webservice"])
        elif parameters.get("--mozilla", False):
            if parameters.get("dev", False) or parameters.get("prod", False):
                mozilla = MOZILLA_DEV_ITEMS_API if parameters.get("dev", False) else MOZILLA_PROD_ITEMS_API
                url = datetime.strftime(self.get_date(), mozilla)
                self.tmp_dir = self.path = self.get_files(url)
            else:
                self.path = parameters["<path>"]
                self.use_tmp = False
            parameters["--item-file-identifier"] = MOZILLA_ITEM_FILE_IDENTIFIER
            parameters["--item"] = MOZILLA_ITEM_FIELD
            parameters["--item-locales"] = MOZILLA_ITEM_LOCALES_FIELD
            parameters["--item-genres"] = MOZILLA_ITEM_GENRES_FIELD
            parameters["--user-file-identifier"] = MOZILLA_USER_FILE_IDENTIFIER
            parameters["--user"] = MOZILLA_USER_FIELD
            parameters["--user-items"] = MOZILLA_USER_ITEMS
            parameters["--user-item-identifier"] = MOZILLA_USER_ITEM_IDENTIFIER
            parameters["--user-item-acquired"] = MOZILLA_USER_ITEM_ACQUISITION_FIELD
            parameters["--user-item-dropped"] = MOZILLA_USER_ITEM_DROPPED_FIELD
            parameters["--date-format"] = MOZILLA_DATE_FORMAT
        elif parameters.get("<path>", False):
            self.path = parameters["<path>"]
            self.use_tmp = False
        self.item_file_identifier_field = parameters["--item-file-identifier"]
        self.item_field = parameters["--item"]
        self.item_locales_field = parameters["--item-locales"]
        self.item_genres_field = parameters["--item-genres"]
        self.user_file_identifier_field = parameters["--user-file-identifier"]
        self.user_field = parameters["--user"]
        self.user_items_field = parameters["--user-items"]
        self.user_item_identifier_field = parameters["--user-item-identifier"]
        self.user_item_acquisition_field = parameters["--user-item-acquired"]
        self.user_item_dropped_field = parameters["--user-item-dropped"]
        self.date_format = parameters["--date-format"]
        if parameters.get("--verbose", False):
            logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s",
                                datefmt="%m-%d-%Y %H:%M:%S",
                                level=logging.DEBUG)

    def walk_files(self):
        for path, _, files in os.walk(self.path):
            for name in files:
                if name[-5:].lower() == ".json":
                    yield "/".join([path, name])

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
        if self.parameters.get("<date>", False):
            return datetime.strptime(self.parameters["<date>"], "%Y-%m.%d").date()
        if self.parameters.get("today", False):
            return date.today()
        return date.today() - timedelta(1)

    def load(self):
        """
        Load the files to db
        """
        logging.debug("Starting")
        if self.path:
            try:
                self.fill_db(self.walk_files())
            finally:
                if self.use_tmp:
                    self.clean_tmp()
                    logging.debug("Tmp files deleted")
                logging.debug("Done!")

    @staticmethod
    def load_files(files):
        """
        Load files to memory
        """
        return (json.load(open(f)) for f in files)

    def fill_db(self, objects):
        """
        Put objects in db
        """
        objects = self.load_files(objects)
        if self.is_item:
            self.fill_db_with_items(objects)
        else:
            self.fill_db_with_users(objects)

    def fill_db_with_items(self, objects):
        """
        Put items in db
        """
        objs = []
        for obj in objects:
            if self.item_file_identifier_field in obj:
                obj[self.item_field] = str(obj[self.item_field])
                objs.append(obj)
        objects = objs
        json_items = {json_item[self.item_field]: json_item for json_item in objects}  # Map items for easy treatment

        items = {item.external_id: item for item in Item.objects.filter(external_id__in=json_items.keys())}
        new_items = {}
        categories = set([])
        locales = set([])
        regions = {}
        with click.progressbar(json_items.items(), label="Loading items") as bar:
            for item_eid, json_item in bar:
                if item_eid not in items:
                    try:
                        name = json_item["name"][json_item["default_locale"]]
                    except (KeyError, TypeError):
                        name = json_item.get("name", "NO NAME")
                    except UnicodeEncodeError as e:
                        logging.error(e)
                        name = "NO NAME"
                    new_items[item_eid] = Item(external_id=item_eid, name=name)

                # In case of json[self.item_genres_field] = None
                json_categories = json_item.get(self.item_genres_field, None) or ()
                if isinstance(json_categories, basestring):
                    categories.add(json_categories)
                else:
                    categories = categories.union(json_item[self.item_genres_field])

                # In case of json[self.item_locales_field] = None
                json_locales = json_item.get(self.item_locales_field, None) or ()
                if isinstance(json_locales, basestring):
                    locales.add(json_locales)
                else:
                    locales = locales.union(json_locales)
                for region in json_item.get("regions", None) or ():
                    try:
                        regions[region["name"]]["items"].append(item_eid)
                    except KeyError:
                        regions[region["name"]] = {"slug": region["slug"], "items": [item_eid]}
        #logging.debug("Items ready to be saved")
        Item.objects.bulk_create(new_items.values())
        #logging.debug("%d new items saved with bulk_create" % len(new_items))

        items.update({item.external_id: item for item in Item.objects.filter(external_id__in=json_items.keys())})

        assert len(items) == len(objects), \
            "Size of items and size of objects are different (%d != %d)" % (len(items), len(objects))

        if "recommendation.diversity" in settings.INSTALLED_APPS:
            #logging.debug("Preparing genres")
            db_categories = self.get_genres(categories)
            self.fill_item_genre(objects, items, db_categories)
            #logging.debug("Genres loaded")

        if "recommendation.language" in settings.INSTALLED_APPS:
            #logging.debug("Preparing languages")
            db_locales = self.get_locales(locales)
            db_regions = self.get_regions(regions)
            self.fill_item_locale(objects, items, db_locales)
            self.fill_item_region(regions, items, db_regions)
            #logging.debug("Locales loaded")

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

            Genre.objects.bulk_create(new_genres.values())
            for genre in Genre.objects.filter(name__in=new_genres):
                genres[genre.name] = genre
        return genres

    @staticmethod
    def get_regions(region_names):
        """
        Get regions from database and create the ones that don't exist.
        :param region_names:
        :return: A dict with regions mapped to their name
        """
        regions = {region.name: region for region in Region.objects.filter(name__in=region_names)}
        if len(regions) != len(region_names):
            new_regions = {}
            for name in region_names:
                slug = region_names[name]["slug"]
                if name not in regions:
                    new_regions[name] = Region(name=name, slug=slug)

            Region.objects.bulk_create(new_regions.values())
            for region in Region.objects.filter(name__in=new_regions):
                regions[region.name] = region
        return regions

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
            if len(language_code) < 3 and len(country_code) < 3:
                json_locales[locale] = (language_code, country_code)
                query_locales = query_locales | Q(language_code=language_code, country_code=country_code)
            else:
                logging.warn("Dropped locale %s for not respecting format XX-XX or XX" % locale)

        locales = {str(locale): locale for locale in Locale.objects.filter(query_locales)}
        if len(locales) != len(locales_names):
            new_locales = []
            new_query = Q()
            for json_locale in locales_names:
                if json_locale not in locales:
                    if json_locale in json_locales:
                        language_code, country_code = json_locales[json_locale]
                        new_locales.append(Locale(language_code=language_code, country_code=country_code))
                        new_query = new_query | Q(language_code=language_code, country_code=country_code)

            Locale.objects.bulk_create(new_locales)
            for locale in Locale.objects.filter(new_query):
                locales[str(locale)] = locale
        return locales

    def fill_item_genre(self, objects, items, genres):
        """
        Fill item genres connection
        :param items:
        :param genres:
        :return:
        """
        query_item_genres = Q()
        item_genres = {}
        for json_item in objects:
            json_genres = json_item.get(self.item_genres_field, None) or ()
            for json_genre in json_genres:
                query_item_genres = \
                    query_item_genres | Q(item_id=items[json_item[self.item_field]].pk, type_id=genres[json_genre].pk)
                item_genres[(items[json_item[self.item_field]].pk, genres[json_genre].pk)] = \
                    ItemGenre(item=items[json_item[self.item_field]], type=genres[json_genre])
        if len(query_item_genres) > 0:
            for item_genre in ItemGenre.objects.filter(query_item_genres):
                del item_genres[item_genre.item_id, item_genre.type_id]
        ItemGenre.objects.bulk_create(item_genres.values())

    def fill_item_locale(self, objects, items, locales):
        """
        Fill item locales connection
        :param items:
        :param locales:
        :return:
        """
        query_item_locales = Q()
        item_locales = {}
        for json_item in objects:
            json_locales = json_item.get(self.item_locales_field, None) or ()
            for locale in json_locales:
                if locale in locales:
                    query_item_locales = query_item_locales | Q(locale_id=locales[locale].pk,
                                                                item_id=items[json_item[self.item_field]].pk)
                    item_locales[locales[locale].pk, items[json_item[self.item_field]].pk] = \
                        ItemLocale(locale=locales[locale], item=items[json_item[self.item_field]])
        if len(query_item_locales) > 0:
            for item_locale in ItemLocale.objects.filter(query_item_locales):
                del item_locales[item_locale.locale_id, item_locale.item_id]
        ItemLocale.objects.bulk_create(item_locales.values())

    @staticmethod
    def fill_item_region(objects, items, regions):
        """
        Fill item locales connection
        :param items:
        :param locales:
        :return:
        """
        query_item_regions = Q()
        item_regions = {}
        with click.progressbar(objects.items(), label="Loading item regions") as bar:
            for region_eid, item in bar:
                region_id = regions[region_eid].pk
                item_regions[region_id] = {
                    items[item_eid].pk: ItemRegion(region_id=region_id, item_id=items[item_eid].pk)
                    for item_eid in item["items"]
                }
                query_item_regions = query_item_regions | Q(region_id=region_id, item_id__in=item_regions[region_id])

        if len(query_item_regions) > 0:
            for item_region in ItemRegion.objects.filter(query_item_regions):
                del item_regions[item_region.region_id][item_region.item_id]
        ItemRegion.objects.bulk_create(itertools.chain(*(ir.values() for ir in item_regions.values())))

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

    def fill_db_with_users(self, objects):
        """
        Put users in Database
        :return:
        """
        size = 0
        user_items = {}
        json_users = []
        regions = {}
        langs = {}
        with click.progressbar(objects, label="Loading users to memory") as bar:
            for obj in bar:
                if self.user_file_identifier_field in obj:
                    user_id = str(obj[self.user_field])
                    for item in obj.get(self.user_items_field, ()):
                        item_id = str(item[self.user_item_identifier_field])
                        user_item = user_id, self.user_item_dropped_field in item
                        try:
                            user_items[item_id].append(user_item)
                        except KeyError:
                            user_items[item_id] = [user_item]
                    size += 1
                    json_users.append(user_id)
                    if "region" in obj:
                        try:
                            regions[obj["region"]].append(user_id)
                        except KeyError:
                            regions[obj["region"]] = [user_id]
                    if "lang" in obj:
                        try:
                            langs[obj["lang"]].append(user_id)
                        except KeyError:
                            langs[obj["lang"]] = [user_id]
        logging.debug("Done!")
        users = {user.external_id: user for user in User.objects.filter(external_id__in=json_users)}
        new_users = {}
        for user_eid in json_users:
            if user_eid not in users:
                new_users[user_eid] = User(external_id=user_eid)
        del json_users
        #logging.debug("Users ready to be saved")
        User.objects.bulk_create(new_users.values())
        for user in User.objects.filter(external_id__in=new_users.keys()):
            users[user.external_id] = user

        assert len(users) == size, \
            "Size of loaded objects and users in db is not the same (%d != %d)" % (len(users), size)

        if "recommendation.language" in settings.INSTALLED_APPS:
            self.fill_user_locale(users, regions, langs)
        #logging.debug("%d new users saved with bulk_create" % len(new_users))

        #logging.debug("Preparing items")
        items = {ieid: iid for ieid, iid in Item.objects.filter(external_id__in=user_items).values_list("external_id",
                                                                                                        "id")}
        r = range(0, len(user_items), 300)
        n = len(r)
        user_items = user_items.items()
        user_items = [user_items[i:i+300] for i in r]
        with click.progressbar(user_items, length=n, label="Load items for user inventory") as bar:
            for user_item in bar:
                self.fill_inventory(users, items, user_item)
                del user_item
        #logging.debug("Items loaded")

    @staticmethod
    def fill_inventory(users, items, user_items):
        """
        Fill the user inventory
        :param users:
        :param items:
        :return:
        """
        inventory = {}
        inventory_query = Q()
        for item_eid, user_inv in user_items:
            try:
                item_id = items[item_eid]
            except KeyError:
                logging.warn("Item with external_id %s does not exist!" % item_eid)
            else:
                users_ids = []
                for user_eid, is_dropped in user_inv:
                    user_id = users[user_eid].pk
                    inventory[item_id, user_id] = Inventory(item_id=item_id, user_id=user_id, is_dropped=is_dropped)
                    users_ids.append(user_id)
                inventory_query = inventory_query | Q(item_id=item_id, user_id__in=users_ids)
        if len(inventory_query) > 0:
            to_delete = Q()
            for inv in Inventory.objects.filter(inventory_query):
                item_user = inv.item_id, inv.user_id
                if item_user in inventory:
                    tmp_inv = inventory[item_user]
                    if inv.is_dropped != tmp_inv.is_dropped:
                        to_delete = to_delete | Q(user_id=inv.user_id, item_id=inv.item_id)
                    else:
                        del inventory[item_user]
            if len(to_delete) > 0:
                Inventory.objects.filter(to_delete).delete()
        Inventory.objects.bulk_create(inventory.values())

    @staticmethod
    def fill_user_locale(users, regions, langs):
        region_query = Q()
        user_regions = {}
        db_regions = {region.slug: region.pk for region in Region.objects.all()}
        with click.progressbar(regions.items(), label="Load user regions inventory") as bar:
            for region, ueis in bar:
                try:
                    region_id = db_regions[region]
                except KeyError:
                    pass
                else:
                    region_query = region_query | Q(region_id=region_id, user_id__in=map(lambda x: users[x].pk, ueis))
                    user_regions[region_id] = {
                        users[user_eid]: UserRegion(user_id=users[user_eid].pk, region_id=region_id)
                        for user_eid in ueis
                    }
        if len(region_query) > 0:
            for ur in UserRegion.objects.filter(region_query):
                del user_regions[ur.region_id][ur.user_id]
        UserRegion.objects.bulk_create(itertools.chain(*(ur.values() for ur in user_regions.values())))

        locale_query = Q()
        user_locales = {}
        db_locales = {str(locale): locale.pk for locale in Locale.objects.all()}
        with click.progressbar(langs.items(), label="Load user locales inventory") as bar:
            for locale, ueis in bar:
                try:
                    locale_id = db_locales[locale]
                except KeyError:
                    pass
                else:
                    locale_query = locale_query | Q(locale_id=locale_id, user_id__in=map(lambda x: users[x].pk, ueis))
                    user_locales[locale_id] = {
                        users[user_eid]: UserLocale(user_id=users[user_eid].pk, locale_id=locale_id)
                        for user_eid in ueis
                    }

        if len(locale_query) > 0:
            for ur in UserLocale.objects.filter(locale_query):
                del user_locales[ur.locale_id][ur.user_id]
        UserLocale.objects.bulk_create(itertools.chain(*(ur.values() for ur in user_locales.values())))


class Command(DocOptCommand):
    docs = __doc__

    def handle_docopt(self, arguments):
        # arguments contains a dictionary with the options
        try:
            fill_command = FillTool(arguments)
            fill_command.load()
        except:
            traceback.print_exception(*sys.exc_info())