'''
Created on Nov 28, 2013

.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

from django.views.generic.base import View, TemplateResponseMixin
from ffos.util.views import JSONResponse
from ffos.models import FFOSUser
import logging

from ffos.recommender.controller import TestController
from ffos.recommender.filters import RepetitionFilter, RandomReranker,\
    RegionReranker

controller = TestController()
controller.registerFilter(RepetitionFilter())
controller.registerReranker(RandomReranker(),RegionReranker())

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
        logging.info('starting')
        user = request.GET.get('user',None)
        number = request.GET.get('n',None)
        result = controller.get_recommendation(user=user,n=int(number))
        logging.info('finished')
        return JSONResponse(result)

