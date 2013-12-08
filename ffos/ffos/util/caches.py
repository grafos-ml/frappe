'''
Provide Cache for django objects

Created on Dec 5, 2013


.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

from datetime import datetime, timedelta
from threading import RLock

MAX_ENTRIES = 100
MAX_TIME = timedelta(hours=1)

class Cache(object):
    '''
    A cache to keep objects so queries can be avoided

    '''

    def __init__(self):
        '''
        Constructor for te simple cache. Just create a bunch of variables.
        '''

        self._obj = {}
        self._usage = []
        self._entries = 0
        self._accesses = 0

        # Some future time so the new data substitute this one
        self._oldest_entry = datetime.now()+timedelta(6*365/12)
        self._lock = RLock()

    def cache_command(self,key,command,args=[],kwargs={},forceit=False,
        resulttype=None):
        '''
        Add a new command to the cache. This command will be held in this cache
        and referenced with the key.

        If the key already exists, it will return False if not it return True.
        However if the force parameter is set to True the old key will be
        removed and always return True.

        **Args**

        key *str*:
            The key to reference the result.

        command *callable*:
            A callable objects to execute. The result of the command should be
            a django queryset.

        args *list*:
            A list of parameters to use with the command. DEFAULT=[]

        kwargs *dict*:
            A dictionary of keyword parameters to use with the command.
            DEFAULT={}

        forceit *bool*:
            A boolean to check if the command should replace the old one or
            not. If True this result will replace any other for the key passed.
            DEFAULT=False

        resulttype *type*:
            The type of the result the query should return. If None is passed
            the object goes at it is. Default None.

        **Returns**

        *resulttype*:
            The object if it successful add the queryset to the cache. If force
            is passed as True it should always result an object.
        '''

        # Check if some data need to be erased
        self.clean()
        with self._lock:
            self._accesses += 1
            if key in self._obj:
                if not forceit:
                    return None
                else:
                    self.remove(key)

            self._usage.append((key,datetime.now()))
            self._obj[key] = command(*args,**kwargs)
            self._entries += 1
        # Forces the execution of the query
        return resulttype(self[key]) if resulttype else self[key]

    def remove(self,*keys):
        '''
        Removes some object referenced with key.

        **Args**

        key *str*:
            The key to remove
        '''
        removed = []
        with self._lock:
            for key in keys:
                if key in self._obj:
                    del self._obj[key]
                    self._entries -= 1
                    removed.append(key)
            self._usage = filter(lambda x: x[0] not in removed, self._usage)
            self.set_oldest()

    def set_oldest(self):
        '''
        Set the time of the oldest object in cache
        '''
        with self._lock:
            if self._entries:
                self._oldest_entry = self._usage[0][1]

    def clean(self):
        '''
        Removes old entries
        '''
        with self._lock:
            limit = datetime.now()-MAX_TIME
            to_remove = filter(lambda x: x[1]<limit,self._usage) \
                if self._usage and self._usage[0]<limit else []
            diference = len(self._usage) - len(to_remove)
            if diference > MAX_ENTRIES:
                to_remove += map(lambda  x: x[1],
                    self._usage[:diference-MAX_ENTRIES])
            self.remove(*to_remove)

    def __getitem__(self, key):
        '''
        Return the object associated with this key
        '''
        return self._obj[key]
