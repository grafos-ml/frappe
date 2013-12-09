'''
Controller system that provides results

Created on Nov 29, 2013


.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

import numpy, random
from django.conf.settings import logging
from ffos import models
from ffos.recommender.caches import RecommendationCache

class InterfaceController(object):
    '''
    An abstract controller
    '''

    def __init__(self,*args,**kwargs):
        '''
        The constructor method.

        **Args**

        args *list*:
            Generic anonymous arguments

        kwargs *dict*:
            Generic arguments
        '''
        self._filters = []
        self._rerankers = []
        self.cache = RecommendationCache()


    def registerFilter(self,filter):
        '''
        Register a filter in this controller queue

        **Args**

        filter *Filter*:
            A filter to add to the controller
        '''
        filter.controller = self
        self._filters.append(filter)


    def unregisterFilter(self,fi):
        '''
        Removes a filter from the queue

        **Args**

        fi *Filter*:
            A filter or filter id to remove from the controller
        '''
        self._filters = filter(lambda x: x != fi, self._filters)

    @property
    def filters(self):
        '''
        A list with all the filters registered in this controller
        '''
        return self._filters[:]

    def registerReranker(self,reranker):
        '''
        Register a reranker for this controller.

        **Args**

        reranker *Reranker*:
            A reranker to add to the controller.
        '''
        reranker.controller = self
        self._rerankers.append(reranker)

    def unregisterReranker(self,reranker):
        '''
        Removes a reranker from the queue

        **Args**

        reranker *Reranker*:
            A reranker or reranker id to remove from the controller
        '''
        self._rerankers = filter(lambda x: x != reranker, self._rerankers)

    @property
    def rerankers(self):
        '''
        A list with all the reranker registered in this controller
        '''
        return self._rerankers[:]

    def get_user_matrix(self,user):
        '''
        Catch the user matrix from database

        **Args**

        user *str*:
            User ID

        **Returns**

        *numpy.matrix*:
            The matrix of users.
        '''
        user = self.cache.get_user(user)
        if self.__class__ == InterfaceController:
            raise TypeError('InterfaceController shouldn\'t be used directly. '
                'Create a new class to extend it instead.')
        else:
            raise NotImplementedError('get_user_matrix was not overwritten '
                'by class %s' % self.__class__)

    def get_apps_matrix(self):
        '''
        Catch the app matrix from database

        **Returns**

        *numpy.matrix*:
            The matrix of apps.
        '''
        if self.__class__ == InterfaceController:
            raise TypeError('InterfaceController shouldn\'t be used directly. '
                'Create a new class to extend it instead.')
        else:
            raise NotImplementedError('get_app_matrix was not overwritten '
                'by class %s' % self.__class__)

    def get_app_significance_list(self,user,apps):
        '''
        Get a List of significance values for each app

        **Args**

        user *numpy.matrix*:
            A one row matrix for one user

        apps *numpy.matrix*:
            A matrix with one row for each app in system

        **Return**

        *numpy.array*:
            An array with the app scores for that user
        '''
        m = (user * apps.transpose())
        return numpy.array(m.tolist()[0])


    def get_recommendation(self,user,n):
        '''
        Method to get recommendation according with some user id

        **Args**

        user *FFOSUser*:
            The user external_id. A way to identify the user.

        n *int*:
            The number of recommendations to give in response.

        **Returns**

        *list*:
            A Python list the recommendation apps ids.
        '''
        result = self.get_app_significance_list(
            self.get_user_matrix(user),self.get_apps_matrix())
        logging.debug('Matrix generated')
        for _filter in self.filters:
            result = _filter(user,result)
        logging.debug('Filters finished')
        for _reranker in self.rerankers:
            result = _reranker(user,result)
        logging.debug('Re-rankers finished')
        return [app_id for app_id, _ in sorted(enumerate(result.tolist()),
            cmp=lambda x,y:-1*cmp(x[1],y[1]))[:n]]


class TestController(InterfaceController):
    '''
    A testing controller. It fetch the matrix and decompose it in to
    app matrix and user matrix.

    @see parent
    '''
    def get_user_matrix(self,user):
        '''
        Catch the user matrix from database

        **Args**

        user *str*:
            User ID

        **Returns**

        *numpy.matrix*:
            The matrix of users.
        '''
        return numpy.matrix([[float(random.randint(1,100))
            for _ in range(0,9)]])

    def get_apps_matrix(self):
        '''
        Generate a random

        **Returns**

        *numpy.matrix*:
            The matrix of apps.
        '''
        return numpy.matrix([[float(random.randint(1,100)) for _ in range(0,9)]
            for _ in range(0,len(models.FFOSApp.objects.all()))])




