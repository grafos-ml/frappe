'''
Created on Nov 28, 2013

.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

from django.views.generic.base import View, TemplateResponseMixin
from django.shortcuts import  Http404
from datetime import datetime as dt
from ffos.util.views import JSONResponse
from ffos.models import FFOSUser
from controller import TestController
from filters import RepetitionFilter, RandomReranker

controller = TestController()
controller.registerFilter(RepetitionFilter())
controller.registerReranker(RandomReranker())



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
        print dt.strftime(dt.now(), '%d-%m-%Y %H:%M:%S starting')
        user = request.GET.get('user',None)
        number = request.GET.get('n',None)
        result = controller.get_recommendation(user,int(number))
        print dt.strftime(dt.now(), '%d-%m-%Y %H:%M:%S finished')
        if user and number:
            return JSONResponse(result)
        raise Http404

