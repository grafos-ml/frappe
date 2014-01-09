#-*- coding: utf-8 -*-
'''
Controller system that provides results

Created on Nov 29, 2013


.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

import random, numpy
from collections import Counter
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

class ReRanker(Filter):
    '''
    Reranker is like a filter but it assumes that the second parameter is a
    sorted list with the app ID as values
    '''

class RegionReRanker(ReRanker):
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
        to_add = []
        for a in self.get_user_pref(user):
            app_score.remove(a.pk)
            to_add.append(a.pk)
        return app_score+to_add

class CategoryReRanker(Filter):
    '''
    Category Reranker. It associates the user app category profile with app
    categories.
    '''

    def __init__(self,n=4):
        self.num_rec = n

    PART = 0.33

    def __call__(self, user,app_score):
        tes = len(app_score)
        ucp = self.get_user_category_profile(user)
        soma, prefs = 0, []
        for cat, mass in ucp:
            soma += int(mass*self.num_rec)
            prefs += [cat] * int(mass*self.num_rec)
            if soma > self.num_rec / 3: break
        acd = self.get_apps_category_dict(app_score)
        toadd = []
        for cat in prefs:
            for aid in acd[cat]:
                if aid not in toadd:
                    toadd.append(aid)
                    break
        for i in toadd:
            app_score.remove(i)
        i = self.num_rec - len(toadd)
        if len(app_score[:i]+toadd+app_score[i:]) != tes:
            from django.shortcuts import Http404
            raise Http404
        return app_score[:i]+toadd+app_score[i:]

    def get_user_category_profile(self,user):
        ucp = cache.get('USER_CATEGORY_PROFILE_%s' % user.external_id)
        if ucp == None:
            appn = user.installed_apps.all().count()
            ucp = sorted([(key[0],float(value)/appn) for key, value in Counter(
                user.installed_apps.values_list('categories__name')).items()],
                cmp=lambda x,y: cmp(y[1],x[1]))
            cache.set('USER_CATEGORY_PROFILE_%s' % user.external_id,ucp)
        return ucp

    def get_apps_category_dict(self,sorted_tlist):
        '''

        Requires sorted_tlist to be a tuple list sorted by the second element of
        the tuple and the first element to be an app primary key

        **Return**

        *Dict*:
            A dictionary with categories as keys and a list of app ids.
        '''
        acd = cache.get('APP_CATEGORY_PROFILE')
        if acd == None:
            part = sorted_tlist[:int(len(sorted_tlist)*CategoryReRanker.PART)]
            rs = FFOSApp.objects.filter(id__in=part).values_list('id',
                'categories__name')
            acd = {}
            for appID, cat in rs:
                acd[cat] = [] if cat not in acd else acd[cat]+[appID]
            cache.set('APP_CATEGORY_PROFILE',acd)
        return acd
