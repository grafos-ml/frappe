#! -*- encoding: utf-8 -*-
"""
Models for Module configuration of frappe system.
"""
__author__ = "joaonrb"

try:
    import cPickle as pickle
except ImportError:
    import pickle
import json
import zlib
from six import string_types
from django.db import models
from django.utils.translation import ugettext as _
from django.utils.six import with_metaclass
from frappe.decorators import Cached


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
        if isinstance(value, string_types):
            return pickle.loads(zlib.decompress(value))
        return value

    def get_prep_value(self, value):
        """
        Prepare the value from python like object to database like value.

        :param value: Matrix to keep in database
        :return: Pickled object.
        """
        return zlib.compress(pickle.dumps(value))


class AlgorithmData(models.Model):
    """
    Data to feed the predictor algorithm
    """

    identifier = models.CharField(_("identifier"), max_length=255)
    data = PythonObjectField(_("data"))
    timestamp = models.DateTimeField(_("timestamp"), auto_now_add=True)

    class Meta:
        verbose_name = _("algorithm data")
        verbose_name_plural = _("algorithm data")

    def __str__(self):
        """
        Algorithm string representation.
        """
        return "%s, %s" % (self.identifier, self.timestamp)

    def __unicode__(self):
        """
        Algorithm string representation.
        """
        return "%s, %s" % (self.identifier, self.timestamp)


class Predictor(models.Model):
    """
    Predictor algorithm.
    """

    identifier = models.CharField(_("identifier"), max_length=255)
    python_class = models.CharField(_("python class"), max_length=255)
    kwargs = models.TextField(_("kwargs"), default="{}")
    data = models.ManyToManyField(AlgorithmData, verbose_name=_("data"))

    class Meta:
        verbose_name = _("predictor")
        verbose_name_plural = _("predictors")

    def __str__(self):
        """
        Predictor string representation.
        """
        return self.identifier

    def __unicode__(self):
        """
        Predictor string representation.
        """
        return self.identifier

    @Cached()
    def get_algorithm(self):
        """
        Return the predictor algorithm
        """
        class_parts = self.python_class.split(".")
        module, cls = ".".join(class_parts[:-1]), class_parts[-1]
        algorithm = getattr(__import__(module), cls)(**json.loads(self.kwargs))
        algorithm.load_from(self.data.order_by("-timestamp")[0].data)
        return algorithm


class Module(models.Model):
    """
    Module holding recommendation configuration.
    """

    identifier = models.CharField(_("identifier"), max_length=255)
    predictors =