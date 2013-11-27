'''
Created on Nov 25, 2013

This is a nose test module for the data loader methods and the loaddata.py
script.

To USE this test module make sure to have installed the "nose" framework and
the django-nose.
Make sure to install the django_nose in the setting files. An set the settings
variable like "TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'".

Then use the command:
 $ python manage.py test
 $ python manage.py test -v <level> -> to use verbose, the verbose can be from
  0 to 3
 $ python manage.py help test -> to check how it work


The tested method will be:
    > ffos.scripts.loaddata.parse
    > ffos.data.load_categories
    > ffos.data.load_device_type
    > ffos.data.load_app_icon
    > ffos.data.load_region
    > ffos.data.load_locale
    > ffos.data.load_preview
    > ffos.data.load_apps
    > ffos.data.load_users

@author: joaonrb
'''

import os, errno
from ffos.models import *
from ffos.scripts import loaddata
from ffos import nosetest, data
from datetime import datetime
from django.utils.timezone import utc
from django.db import connection

APP_FILE_NUM = 2559
USER_FILE_NUM = 35

def safe_remove(path):
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise



class TestParse(object):
    '''
    The parse method only receive a directory path.

    It walk through the directory parsing .json files into Python dictionaries
    and return them in a Python list.

    This class must ensure that, given a directory, it load every json file to
    a dict dictionary. In this test will be 2148 json files.
    '''

    @classmethod
    def setup_class(cls):
        cls.dir_path = os.path.dirname(nosetest.__file__)


    def test_parse_success(self):
        '''
        Test for loaddata.parse success

        Try to load a set of 2148 json files, distributed by 2 directories,
        to a list of json dictionaries with length 2148.
        '''
        result = loaddata.parse(self.__class__.dir_path+'/success_data')
        assert len(result) == USER_FILE_NUM + APP_FILE_NUM  #Known number of files in the test success dir
        for obj in result:
            #Assert that every element is a Dictionary and not some object like
            #None or something
            assert isinstance(obj,dict)

class TestDataEntry(object):
    '''
    Test for app loading, from json files into the database. This test depends
    on the parse method tested in previous class.

    There are 2113 valid app json in the package for testing. All the tests will
    use this data.

    All tests assumes that the database is empty in the beginning of each test.
    '''

    @classmethod
    def setup(cls):
        #management.call_command('flush')
        cursor = connection.cursor()
        #MAX = 500
        cursor.execute("DELETE FROM ffos_ffosappicon")
        #FFOSApp.objects.all().delete()
        cursor.execute("DELETE FROM ffos_ffosapp")
        #FFOSUser.objects.all().delete()
        cursor.execute("DELETE FROM ffos_ffosuser")
        #FFOSAppCategory.objects.all()\
        #    .delete()
        cursor.execute("DELETE FROM ffos_ffosappcategory")
        #FFOSDeviceType.objects.all()\
        #    .delete()
        cursor.execute("DELETE FROM ffos_ffosdevicetype")
        #Region.objects.all().delete()
        cursor.execute("DELETE FROM ffos_region")
        #Locale.objects.all().delete()
        cursor.execute("DELETE FROM ffos_locale")
        #Preview.objects.all().delete()
        cursor.execute("DELETE FROM ffos_preview")
        pass

    @classmethod
    def teardown(cls):
        pass

    @classmethod
    def setup_class(cls):
        cls.dir_path = os.path.dirname(nosetest.__file__)
        cls.apps = loaddata.parse(cls.dir_path+'/success_data/app')
        cls.users = loaddata.parse(cls.dir_path+'/success_data/user')

    '''
    @classmethod
    def teardown_class(cls):
        safe_remove(os.path.dirname(loaddata.__file__)+'/error.log')
    '''


    def test_categories(self):
        '''
        Test for categories loader

        The test will check if the category is well loaded to the database.
        This test assumes that each file in the success app zone has the
        proper format for the ffos app.


        '''
        for js_app in self.apps:
            categories = data.load_categories(js_app)
            js_cats = js_app['categories']
            for cat in categories:
                # Data is not well structured in data type for each field
                assert cat.name in (str(c) for c in js_cats)

    def test_device_type(self):
        '''
        Test for device type loaderbase.

        The test will check if the device type is well loaded to the database.
        This test assumes that each file in the success app zone has the
        proper format for the ffos app.
        '''
        for js_app in self.apps:
            dts = data.load_device_type(js_app)
            js_dts = js_app['device_types']
            for dt in dts:
                assert dt.name in js_dts

    def test_region(self):
        '''
        Test for regions loader database.

        The test will check if the region is well loaded to the database.
        This test assumes that each file in the success app zone has the
        proper format for the ffos app.
        '''
        for js_app in self.apps:
            regions = data.load_region(js_app)
            js_regions = js_app['regions']
            for region in regions:
                assert (region.name,region.mcc,region.adolescent,region.slug) \
                    in [(r['name'],r['mcc'],r['adolescent'],r['slug'])
                    for r in js_regions]


    def test_locale(self):
        '''
        Test for locale loaderbase.

        The test will check if the locale is well loaded to the database.
        This test assumes that each file in the success app zone has the
        proper format for the ffos app.
        '''
        for js_app in self.apps:
            locales = data.load_locale(js_app)
            js_locales = js_app['supported_locales']
            for locale in locales:
                assert locale.name in js_locales

    def test_app_icon(self):
        '''
        Test for app icon loader database.

        The test will check if the icon urls is well loaded to the database.
        This test assumes that each file in the success app zone has the
        proper format for the ffos app.
        '''
        for js_app in self.apps:
            icon = data.load_app_icon(js_app)
            i = js_app['icons']
            assert (icon.size16,icon.size48,icon.size64,icon.size128) \
                == (i['16'],i['48'],i['64'],i['128'])

    def test_preview(self):
        '''
        Test for preview loader database.

        The test will check if the preview is well loaded to the database.
        This test assumes that each file in the success app zone has the
        proper format for the ffos app.
        '''
        for js_app in self.apps:
            previews = data.load_preview(js_app)
            js_previews = js_app['previews']
            for preview in previews:
                assert (preview.filetype,preview.thumbnail_url,
                    preview.image_url,preview.ffos_preview_id,
                    preview.resource_uri) in [(p['filetype'],
                    p['thumbnail_url'],p['image_url'],p['id'],
                    p['resource_uri']) for p in js_previews]

    def test_app(self):
        '''
        Test for app loader database.

        The test will check if the app is well loaded to the database.
        This test assumes that each file in the success app zone has the
        proper format for the ffos app.

        It also test for the app numbers that are loaded to the database
        2113 apps
        '''
        data.load_apps(*self.apps)
        assert len(FFOSApp.objects.all()) == APP_FILE_NUM
        for app in self.apps:
            try:
                db_app = FFOSApp.objects.get(ffos_app_id=int(app['id']))
            except Exception:
                assert False
            else:
                assert True
                assert db_app.premium_type==app['premium_type']
                assert db_app.content_ratings==app['content_ratings']
                assert db_app.manifest_url==app['manifest_url']
                assert db_app.current_version==app['current_version']
                assert db_app.upsold==app['upsold']
                assert db_app.rating_count==app['ratings']['count']
                assert db_app.rating_average==app['ratings']['average']
                assert db_app.app_type==app['app_type']
                assert db_app.author==app.get('author',None)
                assert db_app.support_url==app['support_url']
                assert db_app.slug==app['slug']
                assert db_app.created==datetime.strptime(app['created'],
                        '%Y-%m-%dT%H:%M:%S').replace(tzinfo=utc)\
                        if 'created' in app else None
                assert db_app.homepage==app['homepage']
                assert db_app.support_email==app['support_email']
                assert db_app.public_stats==app['public_stats']
                assert db_app.status==app['status']
                assert db_app.privacy_policy==app['privacy_policy']
                assert db_app.is_packaged==app['is_packaged']
                assert db_app.description==app['description']
                assert db_app.default_locale==app['default_locale']
                assert db_app.price==app['price']
                assert db_app.payment_account==app['payment_account']
                assert db_app.price_locale==app['price_locale']
                assert db_app.name==app['name']
                assert db_app.payment_required==app.get('payment_required',
                    False)
                assert db_app.weekly_downloads==app.get('weekly_downloads',
                    None)
                assert db_app.upsell==app['upsell']
                assert db_app.resource_uri==app['resource_uri']


    def test_user(self):
        '''
        Test for the user loader database

        The test will check if the user is well loaded to the database.
        This test assumes that each file in the success app zone has the
        proper format for the ffos app.

        It also test if the 35 user json files are loaded
        '''
        data.load_apps(*self.apps)
        data.load_users(*self.users)
        assert len(FFOSUser.objects.all()) == USER_FILE_NUM
        for user in self.users:
            try:
                db_user = FFOSUser.objects.get(external_id=user['user'])
            except Exception:
                assert False
            else:
                assert True
                assert db_user.locale==user['lang']
                assert db_user.region==user['region']
                for app in user['installed_apps']:
                    try:
                        db_user.installed_apps.get(
                            installation_date=datetime.strptime(
                                app['installed'],'%Y-%m-%dT%H:%M:%S')
                                .replace(tzinfo=utc),
                            app__ffos_app_id=app['id'])
                    except Exception:
                        assert False
                    else:
                        assert True