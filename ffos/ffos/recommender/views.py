'''
Created on Nov 28, 2013

.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

from django.views.generic.base import View, TemplateResponseMixin
from django.shortcuts import RequestContext, render_to_response, Http404
from django.conf import settings
import json
from ffos.util.views import JSONResponse
from controller import TestController

controller = TestController()



class RecomenderAPI(View, TemplateResponseMixin):

#    template_name = "SomeTemplate.html"

    http_method_names = [
        'get',
#        'post',
#        'put',
#        'patch',
#        'delete',
#        'head',
#        'options',
#        'trace'
        ]

    #def get_context_data(self,request,**kwargs):
    #    context = RequestContext(request)
    #    context.update({'settings': settings})
    #    return context

    def get(self,request,**kwargs):
        '''
        Get the request from the user and response a list of recommendations
        '''
        user = request.GET.get('user',None)
        number = request.GET.get('n',None)
        if user and number:
            return JSONResponse(controller.get_recommendation(user,int(number)))
        raise Http404

