'''
Controller system that provides results

Created on Nov 29, 2013


.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

import numpy, random

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
            app_score[app.pk] = float('-inf')
        return app_score

class RandomReranker(Filter):

    def __call__(self, user,app_score):
        for i in xrange(0,len(app_score)):
            app_score[i] *= random.uniform(1,1.2)
        return app_score