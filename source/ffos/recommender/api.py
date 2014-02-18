#-*- coding: utf-8 -*-
"""
Created on 10 Jan 2014

TastyPie API module or ffos app recommender

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
"""
from tastypie.authorization import Authorization
from ffos.models import FFOSUser
from django.conf.urls import url

from ffos.recommender.controller import SimpleController
from ffos.recommender.filters import RepetitionFilter, RegionReRanker, \
    LocaleFilter, CategoryReRanker, RepetitionReRanker
from ffos.api import FFOSResource

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


class RecommendationResource(FFOSResource):
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

    class WrapView(FFOSResource.WrapView):
        """
        This class is used to wrap the views so they may retrieve parameter data from the url. The default just
        retrieve the format.
        """

        def set_request(self, request, *args, **kwargs):
            """
            Set some request variables to be used in views
            """
            args, kwargs = super(RecommendationResource.WrapView, self).set_request(request, *args, **kwargs)
            request.recommendation_len = int(kwargs.pop('n', 10))
            return args, kwargs

    @property
    def urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<n>[0-9]+)/(?P<external_id>\w[\w/-]*).(?P<format>\w+)$" %
                self._meta.resource_name, self.WrapView(self, "dispatch_detail"), name="api_dispatch_detail")]

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