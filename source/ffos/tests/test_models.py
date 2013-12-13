'''
Created on Dec 5, 2013

This is a nose test module for the data loader methods and the loaddata.py
script.

-------------------------------------------------------------------------------
This test module is to substitute the "deprecated" version in nosetest module
-------------------------------------------------------------------------------

To USE this test module make sure to have installed the "nose" framework and
the django-nose.
Make sure to install the django_nose in the setting files. An set the settings
variable like "TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'".

Then use the command::

    $ python manage.py test

    $ python manage.py test -v <level> -> to use verbose, the verbose can be
    from 0 to 3

    $ python manage.py help test -> to check how it work


The tested method will be:
    > ffos.util.parseDir
    > ffos.models.FFOSApp.load
    > ffos.models.FFOSUser.load - Yet to be implemented


.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>
'''

import os
from ffos.models import *
from ffos import tests
import itertools
from datetime import datetime
from django.utils.timezone import utc
from django.db import connection
from ffos.util import parseDir
from collections import Counter

APP_FILE_NUM = 2559
USER_FILE_NUM = 35

class TestParse(object):
    '''
    The parseDir method only receive a directory path and a sillent variable.

    It walk through the directory parsing .json files into Python dictionaries
    and return them in a Python list.

    This class must ensure that, given a directory, it load every json file to
    a dict dictionary. In this test will be 2594 json files.
    '''
    @classmethod
    def setup_class(cls):
        cls.dir_path = os.path.dirname(tests.__file__)

    def test_parse_success(self):
        '''
        Test for loaddata.parse success

        Try to load a set of 2594 json files, distributed by 2 directories,
        to a list of json dictionaries with length 2594.
        '''
        result = parseDir(self.__class__.dir_path+'/success_data')

        #Known number of files in the test success dir
        assert len(result) == USER_FILE_NUM + APP_FILE_NUM
        for obj in result:
            #Assert that every element is a Dictionary and not some object like
            #None or something
            assert isinstance(obj,dict)


class TestLoad(object):
    '''
    Test the load data methods. This methods are in the the models and are
    called from the Model Class.
    '''
    @classmethod
    def setup(cls):
        '''
        #management.call_command('flush')
        #cursor = connection.cursor()
        #MAX = 500
        #cursor.execute("DELETE FROM ffos_ffosappicon")
        FFOSApp.objects.all().delete()
        #cursor.execute("DELETE FROM ffos_ffosapp")
        FFOSUser.objects.all().delete()
        #cursor.execute("DELETE FROM ffos_ffosuser")
        FFOSAppCategory.objects.all()\
            .delete()
        #cursor.execute("DELETE FROM ffos_ffosappcategory")
        DeviceType.objects.all()\
            .delete()
        #cursor.execute("DELETE FROM ffos_ffosdevicetype")
        Region.objects.all().delete()
        #cursor.execute("DELETE FROM ffos_region")
        Locale.objects.all().delete()
        #cursor.execute("DELETE FROM ffos_locale")
        Preview.objects.all().delete()
        #cursor.execute("DELETE FROM ffos_preview")
        '''

    @classmethod
    def teardown(cls):
        pass

    @classmethod
    def setup_class(cls):
        cls.dir_path = os.path.dirname(tests.__file__)
        cls.apps = parseDir(cls.dir_path+'/success_data/app')
        cls.users = parseDir(cls.dir_path+'/success_data/user')

    def test_apps(self):
        '''
        Test the number of apps to enter actually enter the db.
        Test the number of every element of the app actually enter the db
        Test if the new app in the db are the ones in the queue to enter
        '''
        # Check if tables is empty at the beginning. They Should so this is more
        # to have sure.
        assert len(FFOSApp.objects.all()) == 0
        assert len(FFOSAppCategory.objects.all()) == 0
        assert len(DeviceType.objects.all()) == 0
        assert len(FFOSAppIcon.objects.all()) == 0
        assert len(Region.objects.all()) == 0
        assert len(Locale.objects.all()) == 0
        assert len(Preview.objects.all()) == 0

        json_apps = self.__class__.apps
        FFOSApp.load(*json_apps)
        sorted_app = dict(map(lambda x:(int(x['id']),x), json_apps))
        cat_len = len(Counter(itertools.chain(*map(
            lambda x:FFOSAppCategory.get_obj(x),json_apps))))
        dt_len = len(Counter(itertools.chain(*map(
            lambda x:DeviceType.get_obj(x),json_apps))))
        ai_len = len(Counter(map(lambda x:FFOSAppIcon.identify(
            FFOSAppIcon.get_obj(x)),json_apps)))
        reg_len = len(Counter(map(lambda x: Region.identify(x),
            itertools.chain(*map(lambda x:Region.get_obj(x),json_apps)))))
        loc_len = len(Counter(itertools.chain(*map(lambda x:Locale.get_obj(x),
            json_apps))))
        prev_len = len(Counter(map(lambda x: Preview.identify(x),
            itertools.chain(*map(lambda x:Preview.get_obj(x),json_apps)))))

        apps = FFOSApp.objects.all().prefetch_related('categories','icon',
            'device_types','regions','supported_locales','previews')
        # Check if to more or less objects where loaded to the database
        assert len(apps) == len(json_apps)
        assert len(FFOSAppCategory.objects.all()) == cat_len
        assert len(DeviceType.objects.all()) == dt_len
        assert len(FFOSAppIcon.objects.all()) == ai_len
        assert len(Region.objects.all()) == reg_len
        assert len(Locale.objects.all()) == loc_len
        assert len(Preview.objects.all()) == prev_len
        for app in apps:
            # Check if every app in database is in cls.apps
            assert app.external_id in sorted_app.keys()

            # sort the objects so it is easier to check
            sorted_cat = map(lambda x: FFOSAppCategory.identify(x),
                FFOSAppCategory.get_obj(sorted_app[app.external_id]))
            sorted_dt = map(lambda x: DeviceType.identify(x),
                DeviceType.get_obj(sorted_app[app.external_id]))
            sorted_reg = map(lambda x: Region.identify(x),
                Region.get_obj(sorted_app[app.external_id]))
            sorted_loc = map(lambda x: Locale.identify(x),
                Locale.get_obj(sorted_app[app.external_id]))
            sorted_prev = map(lambda x: Preview.identify(x),
                Preview.get_obj(sorted_app[app.external_id]))

            # Check if all the objects are in db to and all their field are the
            # same as the original
            for obj in app.categories.all():
                assert FFOSAppCategory.identify_obj(obj) in sorted_cat
            assert FFOSAppIcon.identify_obj(app.icon) == \
                FFOSAppIcon.identify(FFOSAppIcon.get_obj(
                sorted_app[app.external_id]))
            for obj in app.device_types.all():
                assert DeviceType.identify_obj(obj) in sorted_dt
            for obj in app.regions.all():
                assert Region.identify_obj(obj) in sorted_reg
            for obj in app.supported_locales.all():
                assert Locale.identify_obj(obj) in sorted_loc
            for obj in app.previews.all():
                assert Preview.identify_obj(obj) in sorted_prev

    def test_user(self):
        # Test if the tables are empty, same has before.
        assert len(FFOSUser.objects.all()) == 0
        assert len(Installation.objects.all()) == 0

        assert len(FFOSApp.objects.all()) != 0

        json_user = self.__class__.users
        FFOSUser.load(*json_user)

        # Sort the users in json
        sorted_user = dict(map(lambda x:(x['user'],x), json_user))

        len_ins = len(Counter(map(lambda x: x['id'], itertools.chain(*map(
            lambda x: x['installed_apps'],json_user)))))

        users = FFOSUser.objects.all().prefetch_related('installed_apps')
        assert len(users) == len(json_user)
        assert len(Installation.objects.all()) == len_ins

        for user in users:
            assert user.external_id in sorted_user.keys()
            app_ids = map(lambda x: x['id'],sorted_user[user.external_id])
            assert len(app_ids) == len(user.installed_apps.all())
            for app in user.installed_apps.all():
                app.external_id in app_ids
