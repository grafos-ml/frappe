#! -*- encoding: utf-8 -*-
"""
Models special fields
"""

from __future__ import division, absolute_import, print_function
try:
    import cPickle as pickle
except ImportError:
    import pickle
import json
import base64 as b64
import zlib
from six import string_types
from django.db import models
from django.utils.six import with_metaclass

__author__ = "joaonrb"


class PythonObjectField(with_metaclass(models.SubfieldBase, models.TextField)):
    """
    Mapped structure to be saved in database.
    """

    description = """Python object field."""
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """
        Convert the value from the database to python like object

        >>> print(PythonObjectField().to_python('{"bool": true, "list": ["list", 1, 1.0], "number": 123,'
        ... '"string": "something"}'))
        Traceback (most recent call last):
            ...
        TypeError: Incorrect padding

        >>> print(PythonObjectField().to_python("eJzTSCkw5ApWT8rPz1HnKjDi8jQw5CoOVs/JLC4B8o25NHIKTLjSjbkSPQ25Et2AGCiZV5"
        ... "qblFoElDbl8jQ0MgapLy4pysxLBwqZAQ0rzs9NLcmA8M25ivUAWBQb8w=="))
        {'list': ['list', 1, 1.0], 'bool': True, 'number': 123, 'string': 'something'}

        :param value: String from database.
        :return: A python objects.
        """
        if isinstance(value, string_types) and value:
            return pickle.loads(zlib.decompress(b64.b64decode(value)))
        return value

    def get_prep_value(self, value):
        """
        Prepare the value from python like object to database like value.

        >>> print(PythonObjectField().get_prep_value({"number": 123, "string": "something", "list": ["list", 1, 1.],
        ... "bool": True}))
        eJzTSCkw5ApWT8rPz1HnKjDi8jQw5CoOVs/JLC4B8o25NHIKTLjSjbkSPQ25Et2AGCiZV5qblFoElDbl8jQ0MgapLy4pysxLBwqZAQ0rzs9NLcmA8M25ivUAWBQb8w==

        :param value: Matrix to keep in database
        :return: Pickled object.
        """
        return b64.b64encode(zlib.compress(pickle.dumps(value)))


class JSONField(with_metaclass(models.SubfieldBase, models.TextField)):
    """
    JSON structure to be saved in database.
    """

    description = """Json field."""
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """
        Convert the value from the database to json.

        >>> print(JSONField().to_python('{"list": ["list", 1, 1.0], "number": 123, "string": "something",'
        ... '"bool": true}'))
        {u'bool': True, u'list': [u'list', 1, 1.0], u'number': 123, u'string': u'something'}

        :param value: String from database.
        :return: A python objects.
        """
        if isinstance(value, string_types) and value:
            return json.loads(value)
        return value

    def get_prep_value(self, value):
        """
        Prepare the value from python dictionary to database like value.

        >>> print(JSONField().get_prep_value({"number": 123, "string": "something", "list": ["list", 1, 1.],
        ... "bool": True}))
        {"bool": true, "list": ["list", 1, 1.0], "number": 123, "string": "something"}

        :param value: Matrix to keep in database
        :return: Pickled object.
        """
        return json.dumps(value)