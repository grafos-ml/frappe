# -*- coding: utf-8 -*-
'''
Created on 29 January 2014

Test the tensorCoFi against the testfm.

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
'''
__author__ = 'joaonrb'


from ffos.models import FFOSUser, FFOSApp, Installation
from ffos.util import parseDir
import pandas as pd
import numpy as np
import subprocess
from ffos import recommender
from pkg_resources import resource_filename
from django.conf import settings
#import test.fm
import jnius
from ffos.recommender.models import TensorModel
import os


class TestTensorCoFi(object):
    '''
    
    '''

    cleans_up_after_itself = True

    @classmethod
    def setup_class(cls):
        #TestLoad.setup_class()
        #FFOSApp.load(*TestLoad.apps)
        #FFOSUser.load(*TestLoad.users)
        """
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
            print out
            raise Exception(err)
        else:
            print out
            """
        #os.environ['CLASSPATH'] = resource_filename(recommender.__name__,'lib/'
        #    'algorithm-1.0-SNAPSHOT-jar-with-dependencies.jar')
        from jnius import autoclass
        cls.JavaTensorCoFi = autoclass('es.tid.frappe.recsys.TensorCoFi')
        cls.FloatMatrix = autoclass('org.jblas.FloatMatrix')
        cls.MySQLDataWriter = autoclass('es.tid.frappe.mysql.MySQLDataWriter')
        pass


    def test_tensor_matrix(self):
        '''
        Tests the tensor matrix against the test.fm matrix
        '''
        # loads installation data to pandas.DataFrame

        users,items = TensorModel.train()
        db_u = TensorModel.objects.get(dim=0).numpy_matrix
        db_a = TensorModel.objects.get(dim=1).numpy_matrix
        #Compare matrix calculated like test.fm to the one from database
        assert np.array_equal(users,db_u)
        assert np.array_equal(items,db_a)





