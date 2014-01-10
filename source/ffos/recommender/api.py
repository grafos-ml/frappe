#-*- coding: utf-8 -*-
'''
Created on 10 Jan 2014

TastyPie API module or ffos app recommender

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
'''

from tastypie.authorization import Authorization
from ffos.models import FFOSUser
from tastypie import fields
from tastypie.resources import Resource,ModelResource, ALL, ALL_WITH_RELATIONS

from ffos.recommender.controller import SimpleController
from ffos.recommender.filters import RepetitionFilter, RegionReRanker, \
    LocaleFilter, CategoryReRanker

controller = SimpleController()
controller.registerFilter(
    RepetitionFilter(),
    LocaleFilter()
)
controller.registerReranker(
    RegionReRanker(),
    CategoryReRanker(n=12)
)


class RecommendationResource(Resource):
    class Meta:
        queryset = FFOSUser.objects.all()
        resource_name = 'recommendation'
        #authorization= Authorization()
        allowed_methods = ['get']
        allow = ['external_id']

    def dehydrate(self, bundle):
        '''
        Calculate the recommendations to the recommendation fields
        '''
        bundle.data['recommendations'] = controller.get_recommendation(
            bundle['user']['external_id'])
        return bundle