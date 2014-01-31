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
from ffos.recommender.models import Factor
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
        USER = 'users'
        ITEM = 'items'

        # Get items from database
        dataframe = pd.DataFrame({key: value for key, value in zip([USER,
            ITEM,'date'],zip(*Installation.objects.all().values_list(
            'user_id','app_id','installation_date')))})
        d, md, rmd = dataframe.to_dict(outtype='list'), {USER: {}, ITEM: {}},\
            {USER: {}, ITEM: {}}
        rows = len(d[USER])
        cls = self.__class__
        ndf = cls.FloatMatrix.zeros(rows,2)
        uid_counter, iid_counter = 1, 1
        for i in xrange(rows):
            try:
                nu = md[USER][d[USER][i]]
            except KeyError:
                md[USER][d[USER][i]] = uid_counter
                rmd[USER][uid_counter] = d[USER][i]
                nu = uid_counter
                uid_counter += 1
            try:
                ni = md[ITEM][d[ITEM][i]]
            except KeyError:
                md[ITEM][d[ITEM][i]] = iid_counter
                rmd[ITEM][iid_counter] = d[ITEM][i]
                ni = iid_counter
                iid_counter += 1
            ndf.put(i,float(nu))
            ndf.put(i+rows,float(ni))
        ndf, rmd

        # train JavaTensor with data
        tensor = cls.JavaTensorCoFi(20,5,0.05,40,
            [len(rmd[USER]),len(rmd[ITEM])])
        tensor.train(ndf)

        # Put model in database
        final_model = tensor.getModel()
        users = self._float_matrix2numpy(final_model.get(0))
        items = self._float_matrix2numpy(final_model.get(1))
        '''writer = cls.MySQLDataWriter(settings.DATABASES['default']['HOST'],
            3306,settings.DATABASES['default']['TEST_NAME'],
            settings.DATABASES['default']['USER'],
            settings.DATABASES['default']['PASSWORD'])
        writer.writeModel(final_model)
        db_u = Factor.objects.get(dimension=0).numpy_matrix
        db_a = Factor.objects.get(dimension=1).numpy_matrix
        # print users,db_u, type(users), type(db_u)
        print items,db_a
        '''
        Factor.objects.create(matrix=items,rows=items.shape[0],
            columns=items.shape[1],dimension=1)
        Factor.objects.create(matrix=users,rows=users.shape[0],
            columns=users.shape[1],dimension=0)
        db_u = Factor.objects.get(dimension=0).numpy_matrix
        db_a = Factor.objects.get(dimension=1).numpy_matrix
        #Compare matrix calculated like test.fm to the one from database
        assert np.array_equal(users,db_u)
        assert np.array_equal(items,db_a)




    def _float_matrix2numpy(self, java_float_matrix):
        '''
        Java Float Matrix is a 1-D array writen column after column.
        Numpy reads row after row, therefore, we need a conversion.
        '''
        columns_input = java_float_matrix.toArray()
        split = lambda lst, sz: [np.fromiter(lst[i:i+sz],dtype=np.float)
            for i in xrange(0, len(lst), sz)]
        cols = split(columns_input, java_float_matrix.rows)
        matrix = np.ma.column_stack(cols)
        return matrix





