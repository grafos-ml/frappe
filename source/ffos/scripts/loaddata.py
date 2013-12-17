#!/usr/bin/env python
#-*- coding: utf-8 -*-
'''
Created on Nov 22, 2013

Script to load data to the database. It is used to load users, apps and apps
installed by the user. Make sure that all the apps that user will have installed
already are in database when user loading time.

The app will search for json files in all the sub-directories. Make sure that only
json files with the format from the first option are the the chosen folder.

> USAGE::

    $ loaddata <type> <directory>

Type
====
Is the type of file it will parse. The two kind of files there is are all json.
OPTIONS: user, app

    user: The user option parse the user files. the format of this files are
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
                    'slug': The slug of the app. It'n an important value.
                },
                More apps with the same format as the last one...
            ]
        }

    app: The app fie as much more information. It is defined as::

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
            "categories": [
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

.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>
'''
import sys, os, traceback

sys.path.append(os.path.dirname(__file__)+'/../../')
os.environ['DJANGO_SETTINGS_MODULE'] = 'ffos.settings'
from ffos.models import FFOSApp, FFOSUser
from ffos.util import parseDir
import logging

if __name__ == '__main__':
    file_type = sys.argv[1]
    directory = sys.argv[2]
    try:
        logging.info('loading files to memory...')
        objects = parseDir(directory)
        if file_type == 'app':
            logging.info('loading apps to database...')
            for app in objects:
                app['id'] = int(app['id'])
                for preview in app['previews']:
                    preview['id'] = int(preview['id'])
            FFOSApp.load(*objects)
        else:
            logging.info('loading users to database...')
            for user in objects:
                for app in user['installed_apps']:
                    app['id'] = int(app['id'])
            FFOSUser.load(*objects)
            #data.load_users(*objects)
    except Exception:
        logging.info('An error occurred during execution. Check the error.log \
            at the package source.scripts')
        traceback.print_exc()
    else:
        print 'all done!'
    
    