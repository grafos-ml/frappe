# -*- coding: utf-8 -*-
"""
Created on 11 February 2014



.. moduleauthor:: joaonrb <joaonrb@gmail.com   >
"""
__author__ = 'joaonrb'

from django.http import HttpResponseRedirect
from recommender.records.decorators import ClickApp


@ClickApp()
def go_to(request):
    """
    Redirect to the following app store url
    :param request: Http request
    """
    return HttpResponseRedirect(request.go_to)