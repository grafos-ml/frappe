'''
FireFox data management module.

Created on Nov 22, 2013

The data module. This provide methods to manage the FFOS data files and
connect to the data base.

Load data is one of the functionality provided by this module.

.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>


'''

import os, sys, traceback, logging

sys.path.append(os.path.dirname(__file__)+'/../')
os.environ['DJANGO_SETTINGS_MODULE'] = 'source.settings'

#sys.stderr = open('error.log','w')

from ffos.models import FFOSUser, FFOSApp, Installation, FFOSAppCategory,\
    FFOSDeviceType, FFOSAppIcon, Region, Locale, Preview
from django.db import transaction, IntegrityError
from django.utils.timezone import utc
from datetime import datetime


def load_categories(app):
    '''
    Check if the app categories are on the database. If they don't then
    they are created.
    
    The transaction is set in auto commit for default. If used alone take that
    in account.
    
    The type of the elements in app.categories must be string and nothing else.
    
    **Args**

    app *dict*:
        The format of the app is defined in load_app documentation.

    **Returns**

    *list*:
        A Python list with the category.
    '''
    return [FFOSAppCategory.objects.get_or_create(name=category)[0]
        for category in app['categories']]
        
        
def load_device_type(app):
    '''
    Check if the app device type are on the database. If they don't then
    they are created.
    
    The transaction is set in auto commit for default. If used alone take that
    in account.
    
    The type of the elements in app.device_types must be string and nothing
    else.
    
    **Args**

    app *dict*:
        The format of the app is defined in load_app documentation.

    **Returns**

    *list*:
        A Python list with the type.
    '''
    return [FFOSDeviceType.objects.get_or_create(name=device_type)[0]
        for device_type in app['device_types']]
        

def load_app_icon(app):
    '''
    Put the app icons in the database.
    
    The transaction is set in auto commit for default. If used alone take that
    in account.
    
    The type of the elements in app.16, app.48, app.64, app.128 must all be
    strings and nothing else.
    
    **Args**

    app *dict*:
        The format of the app is defined in load_app documentation.

    **Returns**

    *source.models.FFOSAppIcon*:
        Return the model object
    '''
    return FFOSAppIcon.objects.create(size16=app['icons']['16'], 
        size48=app['icons']['48'],size64=app['icons']['64'],
        size128=app['icons']['128'])

def load_region(app):
    '''
    Check if the regions are on the database. If they don't then they are
    created.
    
    The transaction is set in auto commit for default. If used alone take that
    in account.
    
    The type of the elements in app.regions must be a Python dictionary with
    the keys mcc, name, adolescent and slug::
    > mcc must be an integer
    > name must be a string
    > adolescent must be boolean
    > slug must be a string
    
    **Args**

    app *dict*:
        The format of the app is defined in load_app documentation.

    **Returns**

    *list*:
        A Python list with the region.
    '''
    return [Region.objects.get_or_create(mcc=region['mcc'],name=region['name'],
        adolescent=region['adolescent'],slug=region['slug'])[0]
        for region in app['regions']]
        

def load_locale(app):
    '''
    Check if the locales are on the database. If they don't then they are
    created.
    
    The transaction is set in auto commit for default. If used alone take that
    in account.
    
    The type of the elements in app.supported_locales must be string and
    nothing else.
    
    **Args**

    app *dict*:
        The format of the app is defined in load_app documentation.

    **Returns**

    *list*:
        A Python list with the locale.
    '''
    return [Locale.objects.get_or_create(name=locale)[0]
        for locale in app['supported_locales']]
        
def load_preview(app):
    '''
    Check if the previews are on the database. If they don't then they are
    created.
    
    The transaction is set in auto commit for default. If used alone take that
    in account.
    
    The type of the elements in app.regions must be a Python dictionary with
    the keys file type, thumbnail_url, image_url, id and resource_ur:

        - File type must be an string.
        - Thumbnail_url must be a string.
        - Image_url must be string.
        - Id must be a integer or a string of a number.
        - Thumbnail_url must be a string.

    **Args**

    app *dict*:
        The format of the app is defined in load_app documentation.

    **Returns**

    *list*:
        A Python list with the preview ids mapped to the previews.
    '''
    return [Preview.objects.get_or_create(filetype=preview['filetype'],
        thumbnail_url=preview['thumbnail_url'],image_url=preview['image_url'],
        ffos_preview_id=preview['id'],resource_uri=preview['resource_uri'])[0]
        for preview in app['previews']]

def load_apps(*apps):
    '''
    Load a list of apps to the data model FFOSApp.

    If the apps parameter is according with the prerequisites (respect the
    format) this function should ENSURE that, if the execution ends normally,
    in the end all the data is available in the database.

    **Args**

    apps *list*:
        A list of Python dictionaries, each one represents an app. Is
        required that each app as the following format::

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

    '''
    #jump = 50
    #for start in xrange(0,len(apps),jump):
    #    _load_apps2(*apps[start:start+jump])
    _load_apps2(*apps)


@transaction.atomic
def _load_apps1(*apps):

    try:
        for app in apps:
            try:
                db_app = FFOSApp.objects.create(
                    premium_type=app['premium_type'],
                    content_ratings=app['content_ratings'],
                    manifest_url=app['manifest_url'],
                    current_version=app['current_version'],
                    upsold=app['upsold'],
                    external_id=app['id'],
                    rating_count=app['ratings']['count'],
                    rating_average=app['ratings']['average'],
                    app_type=app['app_type'],
                    author=app.get('author',None),
                    support_url=app['support_url'],
                    slug=app['slug'],
                    icon=load_app_icon(app),
                    created=datetime.strptime(app['created'],
                        '%Y-%m-%dT%H:%M:%S').replace(tzinfo=utc)
                        if 'created' in app else None,
                    homepage=app['homepage'],
                    support_email=app['support_email'],
                    public_stats=app['public_stats'],
                    status=app['status'],
                    privacy_policy=app['privacy_policy'],
                    is_packaged=app['is_packaged'],
                    description=app['description'],
                    default_locale=app['default_locale'],
                    price=app['price'],
                    payment_account=app['payment_account'],
                    price_locale=app['price_locale'],
                    name=app['name'],
                    payment_required=app.get('payment_required',False), # Choose false because it looks logical
                    weekly_downloads=app.get('weekly_downloads',None),
                    upsell=app['upsell'],
                    resource_uri=app['resource_uri'])
                db_app.categories.add(*load_categories(app))
                db_app.device_types.add(*load_device_type(app))
                db_app.regions.add(*load_region(app))
                db_app.supported_locales.add(*load_locale(app))
                db_app.previews.add(*load_preview(app))

            except IntegrityError:
                sys.stderr.write(' '.join([datetime.strftime(datetime.now(),
                    '%d-%m-%Y %H:%M:%S'),'error: element', app['id'],
                    'violates the db Integrity','\n']))
                traceback.print_exc()
            except Exception as e:
                sys.stderr.write(' '.join([datetime.strftime(datetime.now(),
                    '%d-%m-%Y %H:%M:%S'),'error: element', app['id'],
                    str(e),'\n']))
                traceback.print_exc()
            else:
                print datetime.strftime(datetime.now(), '%d-%m-%Y %H:%M:%S'),\
                    'element', app['id'],'added to the db'
    except Exception as e:
        sys.stderr.write(' '.join([datetime.strftime(datetime.now(),
            '%d-%m-%Y %H:%M:%S'),str(e),'\n']))
        traceback.print_exc()

@transaction.atomic
def _load_apps2(*apps):
    entries = [FFOSApp(
                premium_type = app['premium_type'],
                content_ratings = app['content_ratings'],
                manifest_url = app['manifest_url'],
                current_version = app['current_version'],
                upsold = app['upsold'],
                external_id = app['id'],
                rating_count = app['ratings']['count'],
                rating_average = app['ratings']['average'],
                app_type = app['app_type'],
                author = app.get('author',None),
                support_url = app['support_url'],
                slug = app['slug'],
                icon = load_app_icon(app),
                created = datetime.strptime(app['created'],
                    '%Y-%m-%dT%H:%M:%S').replace(tzinfo=utc)
                    if 'created' in app else None,
                homepage = app['homepage'],
                support_email = app['support_email'],
                public_stats = app['public_stats'],
                status = app['status'],
                privacy_policy = app['privacy_policy'],
                is_packaged = app['is_packaged'],
                description = app['description'],
                default_locale = app['default_locale'],
                price = app['price'],
                payment_account = app['payment_account'],
                price_locale = app['price_locale'],
                name = app['name'],

                # Choose false because it looks logical
                payment_required = app.get('payment_required',False),
                weekly_downloads = app.get('weekly_downloads',None),
                upsell = app['upsell'],
                resource_uri = app['resource_uri'],
                #categories = load_categories(app),
                #device_types = load_device_type(app),
                #regions = load_region(app),
                #supported_locales = load_locale(app),
                #previews = load_preview(app)
            ) for app in apps]
    print datetime.strftime(datetime.now(), '\n%d-%m-%Y %H:%M:%S'),\
            'Apps loaded into models'
    FFOSApp.objects.bulk_create(entries)
    print datetime.strftime(datetime.now(), '\n%d-%m-%Y %H:%M:%S'),\
            'Apps in bd'



@transaction.atomic
def load_users(*users):
    '''
    Load a list of users to the data model FFOSUser. It also make the
    connection to the installed apps.
    
    If the users parameter is according with the prerequisites (respects the
    format and for every installed app that app already is registered in
    database) this function should ENSURE that, if the execution ends normally,
    in the end all the data is available in database.
    
    **Args**

    users *dict*:
        A list with Python dictionaries, each one representing a user.
        Is required that each user as the following format::

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
    '''
    for user in users:
        try:
            db_user = FFOSUser.objects.create(locale=user['lang'],
                region=user['region'],external_id=user['user'])
            for app in user['installed_apps']:
                try:
                    Installation.objects.create(user=db_user,
                    app=FFOSApp.objects.get(external_id=app['id']),
                    installation_date=datetime.strptime(app['installed'],
                    "%Y-%m-%dT%H:%M:%S").replace(tzinfo=utc))
                except FFOSApp.DoesNotExist:
                    logging.warning('The app %s doesn\'t exist' % app['id'])
                    pass
        except IntegrityError:
            logging.error(' '.join(['error: user', user['user'],
                'violates the db Integrity']))
            traceback.print_exc()
        except Exception:
            logging.error(' '.join(['error: user', user['user'],
                'throws an unexpected error']))
            traceback.print_exc()
        else:
            logging.info('user %s added to the db' % app['id'])
