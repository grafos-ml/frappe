'''
Provide Cache for FireFox OS recommendation webservice

Created on Dec 5, 2013


.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

from django.shortcuts import get_object_or_404
from django.core.cache import cache
from ffos.models import FFOSUser, FFOSApp
from functools import wraps

class CacheDecorator(object):
    '''
    Decorator for caching something
    '''

    def __init__(self,func):
        '''
        Constructor. It guard the function on self
        '''
        self.func = func

    def __get__(self, instance, klass):
        if instance is None:
            # Class method was requested
            return self.make_unbound(klass)
        return self.make_bound(instance)

    def make_unbound(self, klass):
        @wraps(self.func)
        def wrapper(*args, **kwargs):
            '''This documentation will vanish :)'''
            raise TypeError(
                'unbound method {}() must be called with {} instance '
                'as first argument (got nothing instead)'.format(
                    self.func.__name__,klass.__name__)
                )
        return wrapper

    def make_bound(self, instance):
        @wraps(self.func)
        def wrapper(*args, **kwargs):
            '''This documentation will disapear :)'''
            return self.to_func(self.func)(instance,*args,**kwargs)
        # This instance does not need the descriptor anymore,
        # let it find the wrapper directly next time:
        setattr(instance, self.func.__name__, wrapper)
        return wrapper

class CacheUser(CacheDecorator):
    '''
    Allow users to be cached
    '''

    USER = 'USER_%s'

    @staticmethod
    def to_func(f):
        def wrapper(*args, **kwargs):
            '''This documentation will disapear :)'''
            u_id = kwargs['user']
            if isinstance(u_id,basestring):
                user = cache.get(CacheUser.USER % u_id)
                if user == None:
                    user = get_object_or_404(FFOSUser,external_id=u_id)
                    cache.set(CacheUser.USER % u_id, user)
                kwargs['user'] = user
            return f(*args,**kwargs)
        return wrapper

class CacheApp(CacheDecorator):
    '''
    Allow apps to be cached
    '''

    APP = 'APP_%s'

    @staticmethod
    def to_func(f):
        def wrapper(*args, **kwargs):
            '''This documentation will disapear :)'''
            a_id = kwargs['app']
            if isinstance(a_id,basestring):
                app = cache.get(CacheApp.App % a_id)
                if app == None:
                    app = get_object_or_404(FFOSUser,external_id=a_id)
                    cache.set(CacheApp.APP % a_id, app)
                kwargs['app'] = app
            return f(*args,**kwargs)
        return wrapper