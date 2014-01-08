#-*- coding: utf-8 -*-
'''
Controller system that provides results

Created on Nov 29, 2013


.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

import random
from django.core.cache import cache
from ffos.models import FFOSApp

class Filter(object):
    '''
    An abstract Filter to be implemented with the real thing.
    '''

    def __eq__(self,other):
        '''
        Compares if two filters are equal.
        '''
        if(self.__class__ == other.__class and self.cmp_params(other)):
            return True

    def __ne__(self,other):
        '''
        Compares if two filters are equal.
        '''
        if(self.__class__ != other.__class or not self.cmp_params(other)):
            return True

    def cmp_params(self,other):
        '''
        Compare the params of this filter with the other one
        '''
        return True


    def __call__(user,app_score):
        '''

        '''
        pass


class RepetitionFilter(Filter):
    '''
    An abstract Filter to be implemented with the real thing.
    '''


    def __call__(self,user,app_score):
        '''

        '''
        for app in user.installed_apps.all():
            app_score[app.pk-1] = float('-inf')
        return app_score

class LocaleFilter(Filter):
    '''
    Remove the list scores if the apps doesn't exist in the user language
    '''

    def get_user_pref(self,user):
        apps = cache.get('USER_LOCALE_%s' % user.external_id)
        if apps == None:
            apps = FFOSApp.objects.exclude(supported_locales__name=user.locale)\
                .distinct()
            cache.set('USER_LOCALE_%s' % user.external_id,apps)
        return apps

    def __call__(self,user,app_score):
        for app in self.get_user_pref(user):
            app_score[app.pk-1] = float('-inf')
        return app_score

class RegionReranker(Filter):
    '''
    Region Filter

    This filter search the user Region in profile by his info and the info of
    the installed apps. Then he make every app that don't are translated in user
    preferences and put it all to half.
    '''

    def get_user_pref(self,user):
        apps = cache.get('USER_REGION_%s' % user.external_id)
        if apps == None:
            apps = FFOSApp.objects.exclude(regions__slug__in=([user.region]
                if user.region else []) + ['worldwide'] ).distinct()
            cache.set('USER_REGION_%s' % user.external_id,apps)
        return apps


    def __call__(self, user,app_score):
        for a in self.get_user_pref(user):
            app_score[a.pk-1] /= 2
        return app_score

class RandomReranker(Filter):

    def __call__(self, user,app_score):
        for i in xrange(0,len(app_score)):
            app_score[i] *= random.uniform(1,1.2)
        return app_score

class CategoryReranker(Filter):
    '''
    Category Reranker. It associates the user app category profile with app
    categories.
    '''

    def __call__(self, user,app_score):
        pass

    def getUserProfile(self,user):
        pass
