'''
Utilities for the views system

Created on Nov 28, 2013

Classes and functions to help view management.

.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

from django.http import HttpResponse
import json

class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """
    def __init__(self, data, **kwargs):
        content = json.dumps(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)