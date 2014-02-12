# -*- coding: utf-8 -*-
"""
FireFox recommender models.

Created on Nov 28, 2013

The data module for recommendation features. Here are defined models to the
data needed for the recommendation tools.

Dome django fields are also defined here.

..moduleauthor:: Joao Baptista <joaonrb@gmail.com>

"""
import os
from ffos import recommender
from ffos.models import FFOSUser, FFOSApp
from pkg_resources import resource_filename
os.environ['CLASSPATH'] = resource_filename(recommender.__name__,
                                            'lib/algorithm-1.0-SNAPSHOT-jar-with-dependencies.jar')
# os.environ["JAVA_OPTS"] = "-Xmx4096M"
from django.db import models
from django.utils.translation import ugettext as _
import base64
import numpy as np
from jnius import autoclass
from django.conf import settings
JavaTensorCoFi = autoclass('es.tid.frappe.recsys.TensorCoFi')
FloatMatrix = autoclass('org.jblas.FloatMatrix')
MySQLDataReader = autoclass('es.tid.frappe.mysql.MySQLDataReader')


class Matrix(models.TextField):
    """
    This Class is a field for the tensor matrix. It is a huge field text
    fields.

    In the Frappe backend it was called Base64Field. This is better I think.
    """

    description = """Matrix for tensor controller to find nice app suggestions"""
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if isinstance(value, basestring):
            value = value.decode('utf8')
            return np.frombuffer(base64.decodestring(value), dtype=np.float64)
        return value

    def get_prep_value(self, value):
        return base64.b64encode(value).encode('utf8')


class TensorModel(models.Model):
    """
    Model to the factors needed to the tensor??????

    setup = models.ForeignKey(Setup) ??????
    """
    dim = models.PositiveIntegerField(_('dim'))
    matrix = Matrix(_('tensor matrix'))
    rows = models.PositiveIntegerField(_('rows'))
    columns = models.PositiveIntegerField(_('columns'))

    class Meta:
        # unique_together = ('setup','dimension')
        verbose_name = _('factor')
        verbose_name_plural = _('factors')

    def __unicode__(self):
        return self.matrix

    @property
    def numpy_matrix(self):
        """
        Shape the matrix in to whatever
        TODO
        """
        self.matrix.shape = self.rows, self.columns
        return np.matrix(self.matrix)

    @staticmethod
    def train():
        reader = MySQLDataReader(settings.DATABASES['default']['HOST'], 3306,
                                 settings.DATABASES['default']['TEST_NAME' if settings.TESTING else 'NAME'],
                                 settings.DATABASES['default']['USER'], settings.DATABASES['default']['PASSWORD'])
        tensor = JavaTensorCoFi(20, 5, 0.05, 40, [len(FFOSUser.objects.all()), len(FFOSApp.objects.all())])
        data = reader.getData()
        tensor.train(data)

        # Put model in database
        final_model = tensor.getModel()
        users = TensorModel._float_matrix2numpy(final_model.get(0))
        items = TensorModel._float_matrix2numpy(final_model.get(1))

        TensorModel.objects.create(matrix=users, rows=users.shape[0], columns=users.shape[1], dim=0)
        TensorModel.objects.create(matrix=items, rows=items.shape[0], columns=items.shape[1], dim=1)
        return users, items

    @staticmethod
    def _float_matrix2numpy(java_float_matrix):
        """
        Java Float Matrix is a 1-D array writen column after column.
        Numpy reads row after row, therefore, we need a conversion.
        """
        columns_input = java_float_matrix.toArray()
        split = lambda lst, sz: [np.fromiter(lst[i:i+sz], dtype=np.float) for i in xrange(0, len(lst), sz)]
        cols = split(columns_input, java_float_matrix.rows)
        matrix = np.ma.column_stack(cols)
        return matrix

from django.contrib import admin
admin.site.register([TensorModel])