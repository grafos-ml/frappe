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

import os, errno
from ffos.models import FFOSApp, FFOSUser
from datetime import datetime
from django.utils.timezone import utc
from django.db import connection
from ffos.util import parseDir

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

