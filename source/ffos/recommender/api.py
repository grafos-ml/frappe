#-*- coding: utf-8 -*-
'''
Created on 10 Jan 2014

TastyPie API module or ffos app recommender

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
'''
'''
from django.shortcuts import Http404
from tastypie.authentication import ApiKeyAuthentication
from tastypie.exceptions import BadRequest, ImmediateHttpResponse
from tastypie.exceptions import Unauthorized
from tastypie import fields
'''
from django.utils.translation import ugettext as _
from tastypie.authorization import Authorization
from tastypie.http import HttpForbidden
from ffos.models import FFOSUser
from django.conf.urls import url
from tastypie.resources import csrf_exempt
from tastypie.resources import ModelResource #, ALL, ALL_WITH_RELATIONS,Resource

from ffos.recommender.controller import SimpleController
from ffos.recommender.filters import RepetitionFilter, RegionReRanker, \
    LocaleFilter, CategoryReRanker, RepetitionReRanker

from ffos.recommender.rlogging.rerankers import SimpleLogReRanker

controller = SimpleController()
controller.registerFilter(
    RepetitionFilter(),
    LocaleFilter()
)
controller.registerReranker(
    RegionReRanker(),
    CategoryReRanker(n=12),
    SimpleLogReRanker(),
    RepetitionReRanker()
)


class RecommendationResource(ModelResource):
    class Meta:
        queryset = FFOSUser.objects.all()
        resource_name = 'recommendation'
        detail_uri_name = 'external_id'
        #authentication = ApiKeyAuthentication()
        authorization = Authorization()
        list_allowed_methods = []
        detail_allowed_methods = ['get']
        fields = ['external_id']
        include_resource_uri = False
        #exclude = ['resource_uri']

    @property
    def urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<n>[0-9]+)/(?P<external_id>\w[\w/-]"
                r"*).(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail")]

    def determine_format(self, request):
        """
        Used to determine the desired format from the request.format
        attribute.
        """
        if hasattr(request, 'format') and request.format in self._meta.serializer.formats:
            return self._meta.serializer.get_mime_for_format(request.format)
        return super(RecommendationResource, self).determine_format(request)

    def wrap_view(self, view):
        @csrf_exempt
        def wrapper(request, *args, **kwargs):
            request.format = kwargs.pop('format', None)
            request.recommendation_len = int(kwargs.pop('n', 10))
            wrapped_view = super(RecommendationResource, self).wrap_view(view)
            return wrapped_view(request, *args, **kwargs)
        return wrapper

    def dehydrate(self, bundle):
        """
        Calculate the recommendations to the recommendation fields
        """
        bundle.data['recommendations'] = controller.get_external_id_recommendations(user=bundle.data['external_id'],
                                                                                    n=bundle.request.recommendation_len)
        return bundle
    '''
    def dispatch_list(self, request, **kwargs):
        return self.create_response(
            request,'List recommendations is not a thing. Try something more '
                'specific. If your having troubles just go to the documentation',
            response_class = HttpForbidden
        )
    '''
    """
    def obj_create(self, bundle, **kwargs):
        return super(RecommendationResource, self).obj_create(bundle,
            user=bundle.request.user)

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(user=request.user)
    """