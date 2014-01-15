#-*- coding: utf-8 -*-
'''
FireFox recommender models.

Created on Nov 28, 2013

The data module for recommendation features. Here are defined models to the
data needed for the recommendation tools.

Dome django fields are also defined here.

..moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

from django.db import models
from django.utils.translation import ugettext as _
import base64, numpy

class Matrix(models.TextField):
    '''
    This Class is a field for the tensor matrix. It is a huge field text
    fields.

    In the Frappe backend it was called Base64Field. This is better I think.
    '''

    description = """Matrix for tensor controller to find nice app
        sugestions"""
    __metaclass__ = models.SubfieldBase

    def get_db_prep_save(self, value, connection):
        return base64.encodestring(value)

    def to_python(self,value):
        return base64.decodestring(value)

class Factor(models.Model):
    '''
    Model to the factors needed to the tensor??????

    setup = models.ForeignKey(Setup) ??????
    '''
    dimension = models.PositiveIntegerField(_('dimension'))
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
        '''
        Shape the matrix in to whatever
        TODO
        '''
        matrix = numpy.frombuffer(self.matrix,dtype=numpy.float64)
        matrix.shape = self.rows,self.columns
        return numpy.matrix(matrix)

from django.contrib import admin
admin.site.register([Factor])