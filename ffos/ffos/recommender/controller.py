'''
Controller system that provides results

Created on Nov 29, 2013


.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

import numpy, random
from ffos import models

class InterfaceController(object):
    '''
    An abstract controller
    '''

    def get_recommendation(self,user,number_of_recommendations):
        '''
        Method to get recommendation according with some user id

        **Args**

        user *str*:
            The user external_id. A way to identify the user.

        number_of_recommendations *int*:
            The number of recommendations to give in response.

        **Returns**

        *list*:
            A Python list the recommendation apps ids.
        '''
        if self.__class__ == InterfaceController:
            raise TypeError('InterfaceController shouldn\'t be used directly. '
                'Create a new class to extend it instead.')
        else:
            raise NotImplementedError('get_recommendation was not overwritten '
                'by class %s' % self.__class__)


class TestController(InterfaceController):
    '''
    A testing controller. It fetch the matrix and decompose it in to
    app matrix and user matrix.

    @see parent
    '''

    def get_recommendation(self,user,number_of_recommendations):
        '''
        The matrices will be generated randomly and the it doesn't even connect
        to the database.
        '''
        apps = [app for app in models.FFOSApp.objects.all()]

        users_matrix = numpy.matrix([[random.randint(1,100)
            for _ in range(0,9)]])
        apps_matrix = numpy.matrix([[random.randint(1,100)
            for _ in range(0,9)] for _ in apps])
        m = (users_matrix * apps_matrix.transpose())
        m.sort()
        return numpy.array(m)[0][:number_of_recommendations].tolist()


class TestControllerWithFilters(InterfaceController):
    '''
    A testing controller. It fetch the matrix and decompose it in to
    app matrix and user matrix.

    @see parent
    '''

    def get_recommendation(self,user,number_of_recommendations):
        '''
        The matrices will be generated randomly and the it doesn't even connect
        to the database.
        '''
        pass



