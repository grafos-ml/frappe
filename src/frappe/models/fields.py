#! -*- encoding: utf-8 -*-
"""
Models special fields
"""
__author__ = "joaonrb"

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


class PythonObjectField(with_metaclass(models.SubfieldBase, models.TextField)):
    """
    Mapped structure to be saved in database.
    """

    description = """Python object field."""
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """
        Convert the value from the database to python like object

        :param value: String from database.
        :return: A python objects.
        """
        if isinstance(value, string_types) and value:
            return pickle.loads(zlib.decompress(b64.b64decode(value)))
        return value

    def get_prep_value(self, value):
        """
        Prepare the value from python like object to database like value.

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

        :param value: String from database.
        :return: A python objects.
        """
        if isinstance(value, string_types) and value:
            return json.loads(value)
        return value

    def get_prep_value(self, value):
        """
        Prepare the value from python dictionary to database like value.

        :param value: Matrix to keep in database
        :return: Pickled object.
        """
        return json.dumps(value)