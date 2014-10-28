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
from django.db.models.signals import pre_save
from django.dispatch import receiver
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


class PythonObject(models.Model):
    """
    Python object
    """

    identifier = models.CharField(_("identifier"), max_length=255)
    obj = PythonObjectField(_("object"))

    class Meta:
        verbose_name = _("python object")
        verbose_name_plural = _("python objects")

    def __str__(self):
        """
        Object string representation.
        """
        return self.identifier

    def __unicode__(self):
        """
        Object string representation.
        """
        return self.identifier

    @staticmethod
    @Cached()
    def get_object(object_id):
        return PythonObject.objects.get(pk=object_id).obj


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

    @staticmethod
    @Cached()
    def get_algorithm(module_id, predictor_id):
        """
        Return the predictor algorithm
        """
        items = Module.get_items(module_id)
        predictor = Predictor.objects.get(pk=predictor_id)
        class_parts = predictor.python_class.split(".")
        module, cls = ".".join(class_parts[:-1]), class_parts[-1]
        algorithm = getattr(__import__(module), cls)(**json.loads(predictor.kwargs))
        algorithm.load_from(predictor.data.order_by("-timestamp")[0].data, items=items)
        return algorithm

    @staticmethod
    @Cached()
    def get_predictor(predictor_id):
        """
        Return the predictor
        """
        return Predictor.objects.get(pk=predictor_id)


@receiver(pre_save, sender=Predictor)
def check_predictor(sender, instance, using, **kwarg):
    class_parts = instance.python_class.split(".")
    module, cls = ".".join(class_parts[:-1]), class_parts[-1]
    getattr(__import__(module), cls)(**json.loads(instance.kwargs))


class Module(models.Model):
    """
    Module holding recommendation configuration.
    """

    identifier = models.CharField(_("identifier"), max_length=255)
    predictors = models.ManyToManyField(Predictor, verbose_name=_("predictors"), related_name="modules")
    aggregator = models.TextField(_("aggregator"))
    filters = models.ManyToManyField(PythonObject, verbose_name=_("filters"), related_name="module_as_filter")
    rerankers = models.ManyToManyField(PythonObject, verbose_name=_("re-rankers"), related_name="module_as_reranker")

    class Meta:
        verbose_name = _("module")
        verbose_name_plural = _("modules")

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

    def predict_scores(self, user, size):
        """
        Predict score
        :param user: User to get recommendation
        :param size: Size of requested recommendation
        :return: A list with recommendation
        """
        recommendations = {
            Predictor.get_predictor(predictor_id): Predictor.get_algorithm(self.pk, predictor_id)(user, size)
            for predictor_id in self.get_predictors(self.pk)
        }
        recommendation = self.aggregate(recommendations)
        for rfilter in self.get_filters(self.pk):
            recommendation = rfilter(recommendation, size)
        for reranker in self.get_re_renkers(self.pk):
            recommendation = reranker(recommendation, size)
        return recommendation

    @staticmethod
    @Cached()
    def get_predictors(module_id):
        """
        Get all predictors for this module
        :param module_id:
        :return:
        """
        return [pid for pid, in Predictor.objects.filter(modules_id=module_id).values_list("pk")]