#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created at March 5, 2014

Script to load data to the database. It is used to load users, apps and apps
installed by the user. Make sure that all the apps that user will have installed
already are in database when user loading time.

The app will search for json files in all the sub-directories. Make sure that only
json files with the format from the first option are the the chosen folder.

> USAGE::

    $ fill <type> <directory>

Type
====
Is the type of file it will parse. The two kind of files there is are all json.
OPTIONS: users, items

    users: The user option parse the user files. the format of this files are
    defined as::

        {
            'lang': two or five size string in the locale format,
            'region': Although I think this is just a 2 string code of the region,
                it allow far more (255 length),
            'user': Is a big string, documented as a md5 hash with size 35, but the
                dummy data has far more than that. To play it safe we use 255.
            'installed_apps': [
                {
                    'installed': The date when the app was installed in the format
                        "yyyy-mm-ddThh:mm:ss",
                    'id': The id of the installed app. This should be already on
                        the database.
                    'slug': The slug of the app. It's an important value.
                },
                More apps with the same format as the last one...
            ]
        }

    items: The app fie as much more information. It is defined as::

        {
            "premium_type": String(255),
            "content_ratings": String(255),
            "manifest_url": String(url),
            "current_version": String(10),
            "upsold": String(255),
            "id": String(20) or Integer(20),
            "ratings": {
                "count": Integer(10),
                "average": float(10,3)
            },
            "app_type": String(255),
            "author": String(255),
            "support_url": String(url),
            "slug": String(255),
            "regions": [
                {
                    "mcc": Integer(20),
                    "name": String(255),
                    "adolescent": boolean,
                    "slug": String(5)
                },...
            ],
            "icons": {
                "16": String(url),
                "48": String(url),
                "64": String(url),
                "128": String(url)
            },
            "created": The date when the app was installed in the format
                "yyyy-mm-ddThh:mm:ss",
            "homepage": String(url),
            "support_email": String(255),
            "public_stats": boolean,
            "status": integer(4),
            "privacy_policy": String(255),
            "is_packaged": boolean,
            "description": text,
            "default_locale": String(5),
            "price": String(255),
            "previews": [
                {
                    "filetype": String(255),
                    "thumbnail_url": String(url),
                    "image_url": String(url),
                    "id": String(20) or Integer(20),
                    "resource_uri": String(255)
                },...
            ],
            "payment_account": String(255),
            "genres": [
                String(255),
                ...
                ],
            "supported_locales": [
                String(5),
                ...
                ],
            "price_locale": String(255),
            "name": "String(255),
            "versions": {
                Whatever, this is not going to be use for now
            },
            "device_types": [
                String(255),
                ...
            ],
            "payment_required": boolean,
            "weekly_downloads": String(255),
            "upsell": boolean,
            "resource_uri": String(255)
        }

Directory
=========
The directory to look for the files. The script will try to search for files
in all sub-directories.


.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

# Configure here the Django settings file location
DJANGO_SETTINGS = "firefox.settings"

import sys
import os
import json
import traceback
from pkg_resources import resource_filename
sys.path.append(resource_filename(__name__, "/../"))
os.environ["DJANGO_SETTINGS_MODULE"] = DJANGO_SETTINGS
from django.utils.timezone import utc
from datetime import datetime
from django.db import connection
from firefox.models import ItemDetail
from recommendation.models import Item, User, Inventory
from recommendation.diversity.models import Genre
from recommendation.language.models import Locale

BULK_QUERY = "INSERT INTO %(table)s %(columns)s VALUES %(values)s;"


def parse_dir(directory):
    """
    parse a file into objects
    :param directory: Directory were is the objects
    :return: list of objects
    """
    i = 0
    for path, _, files in os.walk(directory):
        for name in files:
            if name[-5:].lower() == '.json':
                f = '/'.join([path, name])
                yield json.load(open(f))
                i += 1
    print("Files loaded in to memory ...")


def put_items(objects):
    """
    Loads items to the recommendation and FireFox system.

    :param objects: Generator with json objects to put in database
    """
    print("Loading files into memory")
    object_genres = set([])
    object_locales = set([])
    items = {}

    # Create the items
    for json_item in objects:
        external_id = json_item.get("id")
        description = json_item.get("description")
        details = "https://marketplace.firefox.com%s" % json_item.get("resource_uri", "")
        slug = json_item.get("slug")
        name = json_item.get("name")
        genres = []
        for genre in json_item.get("categories", ()):
            genres.append(genre)
            object_genres.add(genre)
        locales = set([])
        for locale in json_item.get("supported_locales", ()):
            locale = locale.lower()
            try:
                loc_code, coun_code = locale.split("-")
                if len(coun_code) > 2:
                    coun_code = ""
            except ValueError:
                loc_code, coun_code = locale.strip("-"), ""
            locale = loc_code, coun_code
            locales.add(locale)
            object_locales.add(locale)
        items[external_id] = Item(external_id=external_id, name=name), genres, locales, (description, details, slug)

    items_in_db = \
        [item for item, in Item.objects.filter(external_id__in=items.keys()).values_list("external_id")]
    missing_items = [item for external_id, item in items.items() if external_id not in items_in_db]
    new_items = {item.external_id: item for item, _, _, _ in missing_items}
    Item.objects.bulk_create(new_items.values())
    new_items = {
        eid: iid for eid, iid in Item.objects.filter(external_id__in=new_items.keys()).values_list("external_id", "id")
    }
    print("New items created ...")

    # Get the genres already in database
    genres = {genre.name: genre for genre in Genre.objects.filter(name__in=object_genres)}

    # Create the missing genres
    missing_genres = [name for name in object_genres if name not in genres]
    new_genres = [Genre(name=name) for name in missing_genres]
    Genre.objects.bulk_create(new_genres)
    for genre in Genre.objects.filter(name__in=missing_genres):
        genres[genre.name] = genre

    print("New genres created ...")

    locales = [locale for locale in Locale.objects.all().values_list("language_code", "country_code")]

    # Create locales
    new_locales = []
    for locale in object_locales:
        if locale not in locales:
            language_code, country_code = locale
            new_locale = Locale(language_code=language_code, country_code=country_code)
            new_locales.append(new_locale)

    Locale.objects.bulk_create(new_locales)

    print("New locales created ...")

    cursor = connection.cursor()
    # Create genre relations
    if new_items:
        relation = []
        for item_eid, item_id in new_items.items():
            for genre in items[item_eid][1]:
                relation.append("(%s, %s)" % (str(genres[genre].id), item_id))
        cursor.execute(BULK_QUERY % {
            "table": "diversity_genre_items",
            "columns": "(genre_id, item_id)",
            "values": ", ".join(relation)})
        print("New genre relations created ...")

    # Create locale relations
    if new_locales:
        locales = {(locale.language_code, locale.country_code): locale for locale in Locale.objects.all()}
        relations = []
        for item_eid, item_id in new_items.items():

            for locale in items[item_eid][2]:
                relations.append("(%s, %s)" % (str(locales[locale].id), item_id))

        cursor.execute(BULK_QUERY % {
            "table": "language_locale_items",
            "columns": "(locale_id, item_id)",
            "values": ", ".join(relations)})
        print("New locale relations created ...")

    # Create details
    details_in_db = [eid for eid in ItemDetail.objects.filter(external_id__in=items.keys()).values_list("external_id")]
    details_to_enter = [external_id for external_id in items.keys() if external_id not in details_in_db]
    items_with_no_detail = {
        eid: iid for eid, iid in Item.objects.filter(external_id__in=details_to_enter).values_list("external_id", "id")
    }
    details = []
    for external_id in details_to_enter:
        description, url, slug = items[external_id][3]
        if description:
            description = str(description) if sys.version_info >= (3, 0) else url.encode('utf-8')
            # description = bytes(description, "utf-8").decode("unicode_escape")
            description = description.replace('"', "'")
        url = (bytes(url, "utf-8") if sys.version_info >= (3, 0) else url.encode('utf-8')).decode("unicode_escape")
        details.append('(%s, "%s", "%s", "%s")' % (str(items_with_no_detail[str(external_id)]), description, url, slug))
    cursor.execute(BULK_QUERY % {
        "table": "firefox_itemdetail",
        "columns": "(item_ptr_id, description, url, slug)",
        "values": ", ".join(details)
    })
    print("New details created ...")


def put_users(objects):
    """
    Loads users for the FireFox recommendation
    :param objects: Users
    :return:
    """
    print("Loading files into memory ...")
    new_users = []
    inventory = {}
    user_locales = {}
    locales_to_enter = set([])
    users = set([])
    items = set([])
    for user in objects:
        external_id = user["user"]
        new_users.append(User(external_id=external_id))
        users.add(external_id)
        for item in user["installed_apps"]:
            items.add(item["id"])
            inventory[(external_id, item["id"])] = datetime.strptime(item["installed"], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=utc)
        # Import locales
        locales = user["lang"]
        if isinstance(locales, str):
            locales = [locales]
        elif isinstance(locales, dict):
            locales = list(locales.values())
        elif not isinstance(locales, list):
            locales = []
        for locale in locales:
            locale = locale.lower()
            try:
                l, c = locale.split("-")
                if len(c) > 2:
                    c = ""
            except ValueError:
                l, c = locale.strip("-"), ""
            locale = l, c
            try:
                user_locales[external_id].add(locale)
            except KeyError:
                user_locales[external_id] = set([locale])
            locales_to_enter.add(locale)


    database_users = User.objects.filter(external_id__in=users).values_list("external_id", "id")
    users_in_db = {eid: iid for eid, iid in database_users}
    new_users = [user for user in new_users if user.external_id not in users_in_db.keys()]
    User.objects.bulk_create(new_users)
    print("Users created ...")

    # Create locales
    locales = [(locale.language_code, locale.country_code) for locale in Locale.objects.all()]
    new_locales = []
    for locale in locales_to_enter:
        if locale not in locales:
            language_code, country_code = locale
            new_locale = Locale(language_code=language_code, country_code=country_code)
            new_locales.append(new_locale)

    Locale.objects.bulk_create(new_locales)

    print("New locales created ...")

    # Create locale relations
    locales = {(locale.language_code, locale.country_code): locale.id for locale in Locale.objects.all()}
    user_to_locales = User.objects.filter(external_id__in=user_locales).values_list("external_id", "id")
    bulk_locale_user = []
    for ueid, uid in user_to_locales:
        for locale in user_locales[ueid]:
            bulk_locale_user.append('("%s", "%s")' % (locales[locale], uid))

    cursor = connection.cursor()
    if len(bulk_locale_user) > 0:
        cursor.execute(BULK_QUERY % {
            "table": "language_locale_users",
            "columns": "(locale_id, user_id)",
            "values": ", ".join(bulk_locale_user)})
    print("New locale relations created ...")

    # Create inventory
    database_items = Item.objects.filter(external_id__in=[str(i) for i in items]).values_list("external_id", "id")
    items = {int(eid): iid for eid, iid in database_items}
    database_users = \
        User.objects.filter(external_id__in=[user.external_id for user in new_users]).values_list("external_id", "id")
    users = {eid: iid for eid, iid in database_users}
    users.update(users_in_db)
    inventory_to_enter = []
    for (uid, iid), date in inventory.items():
        try:
            inventory_to_enter.append(Inventory(user_id=users[uid], item_id=items[int(iid)], acquisition_date=date))
        except KeyError:
            print(" - Item with external id %d doesn't exist" % iid)
        if len(inventory_to_enter) > 1000:
            Inventory.objects.bulk_create(inventory_to_enter)
            inventory_to_enter = []
    Inventory.objects.bulk_create(inventory_to_enter)
    print("Inventory created ...")


TYPE_METHOD = {
    "items": put_items,
    "users": put_users
}


def main(obj_type, directory):
    """
    The main method

    :param obj_type:
    :param objects:
    :return:
    """
    try:
        objects = list(parse_dir(directory))
        for i in range(0, len(objects), 100):
            j = i+100
            TYPE_METHOD[obj_type](objects[i:j])
    except KeyError:
        print("Wrong parameter for data type")
        traceback.print_exc()
    except Exception:
        print("An error occurred during execution. Check the error.log at the package source.scripts")
        traceback.print_exc()
    else:
        print("all done!")


# Script main

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
