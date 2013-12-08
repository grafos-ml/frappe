'''
Provide Cache for FireFox OS recommendation webservice

Created on Dec 5, 2013


.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

from django.shortcuts import get_object_or_404
from ffos.util.caches import Cache
from ffos.models import FFOSUser, FFOSApp


class RecommendationCache(Cache):
    '''
    A special Cache for the recommendation controller
    '''

    ALL_USERS = 'ALL USERS'
    ALL_APPS = 'ALL APPS'
    USER = 'USER %s'
    APP = 'APP %s'


    def get_all_users(self,force=False):
        '''
        Return all users. If force is passed with True another sql request is
        made

        **Args**

        force *bool*:
            If another query should be made or not.

        **Return**

        *list*:
            A list with all the users.
        '''
        if force:
            return self.cache_command(self.ALL_USERS,list,FFOSUser.objects.all)
        try:
            return self[self.ALL_USERS]
        except KeyError:
            return self.get_all_users(force=True)

    @property
    def all_users(self):
        '''
        Return all users in cache
        '''
        return self.get_all_users()

    def get_all_apps(self,force=False):
        '''
        Return all apps. If force is passed with True another sql request is
        made

        **Args**

        force *bool*:
            If another query should be made or not.

        **Return**

        *list*:
            A list with all the apps.
        '''
        if force:
            return self.cache_command(self.ALL_APPS,list,FFOSApp.objects.all)
        try:
            return self[self.ALL_APPS]
        except KeyError:
            return self.get_all_apps(force=True)

    @property
    def all_apps(self):
        '''
        Return all apps in cache
        '''
        return self.get_all_apps()


    def get_user(self,user,force=False):
        '''
        Return user with external id. If force is passed with True another sql
        request is made.

        **Args**

        user *str*:
            User external id.

        force *bool*:
            If another query should be made or not.

        **Return**

        *FFOSUser*:
            The user.
        '''
        user_id = self.USER % user
        if force:
            return self.cache_command(user_id,get_object_or_404,
                args=[FFOSUser],kwargs={'external_id': user})
        try:
            return self[user_id]
        except KeyError:
            return self.get_user(user,force=True)

    def get_app(self,app,force=False):
        '''
        Return app. If force is passed with True another sql request is
        made.

        **Args**

        app *str*:
            App external id.

        force *bool*:
            If another query should be made or not.

        **Return**

        *FFOSApp*:
            The App.
        '''
        app_id = self.APP % app
        if force:
            return self.cache_command(app_id,get_object_or_404,
                args=[FFOSApp], kwargs={'external_id': app})
        try:
            return self[app_id]
        except KeyError:
            return self.get_app(app,force=True)






