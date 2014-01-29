# -*- coding: utf-8 -*-
'''
Created on 29 January 2014

Test the tensorCoFi against the testfm.

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
'''
__author__ = 'joaonrb'


from ffos.tests.test_models import TestLoad
from ffos.models import FFOSUser, FFOSApp, Installation
from ffos.util import parseDir
import pandas as pd
import numpy as np
import subprocess
from ffos import recommender
from pkg_resources import resource_filename
from django.conf import settings
#import test.fm

class TestTensorCoFi(object):
    '''
    
    '''

    cleans_up_after_itself = True

    @classmethod
    def setup_class(cls):
        TestLoad.setup_class()
        FFOSApp.load(*TestLoad.apps)
        FFOSUser.load(*TestLoad.users)
        sub = subprocess.Popen(['java','-cp',
            resource_filename(recommender.__name__,'lib/'
            'algorithm-1.0-SNAPSHOT-jar-with-dependencies.jar'),
            'es.tid.frappe.mysql.ModelBuilder','-n',
            settings.DATABASES['default']['TEST_NAME'],
            '-h',settings.DATABASES['default']['HOST'],'-u',
            settings.DATABASES['default']['USER'],'-w',
            settings.DATABASES['default']['PASSWORD']],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = sub.communicate()
        if err:
            raise Exception(err)
        else:
            print out


    def test_tensor_matrix(self):
        '''
        Tests the tensor matrix against the test.fm matrix
        '''
        # loads installation data to pandas.DataFrame
        idata = pd.DataFrame({key: value for key, value in zip(['users','items',
            'date'],zip(*Installation.objects.all().values_list(['user_id',
            'app_id','installation_date'])))})



