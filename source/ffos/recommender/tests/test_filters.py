#-*- coding: utf-8 -*-
'''
Created on 8 Jan 2014

Tests for filters and re-rankers

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
'''

from ffos.tests.test_models import TestLoad
from ffos.models import FFOSUser, FFOSApp
from ffos.util import parseDir
from ffos.recommender.filters import CategoryReRanker

class TestCategoryReRanker(object):
    '''
    Test the category reranker
    '''

    @classmethod
    def teardown(cls):
        pass

    @classmethod
    def setup_class(cls):
        TestLoad.setup()
        FFOSApp.load(*parseDir(TestLoad.__class__.apps))
        FFOSUser.load(*parseDir(TestLoad.__class__.users))


    def test_getUserCategoryProfile(self):
        '''
        I need some benchmark data to make good tests
        '''
        rr = CategoryReRanker(n=4)
        user = FFOSUser.objects.get(external_id='006a508fe63e87619db5c3db21da2c'
            '536f24e296c29d885e4b48d0b5aa561173')
        assert(isinstance(rr.get_user_category_profile(user), dict))



