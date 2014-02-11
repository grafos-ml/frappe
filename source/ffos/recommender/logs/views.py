# -*- coding: utf-8 -*-
'''
Created on 11 February 2014



.. moduleauthor:: joaonrb <joaonrb@gmail.com   >
'''
__author__ = 'joaonrb'

from django.http import HttpResponseRedirect
from ffos.recommender.logs.decorators import ClickApp

@ClickApp
def goto(request):
    """
    Redirect to the following app store url
    """
    return HttpResponseRedirect(request.go_to)