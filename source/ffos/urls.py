from django.conf.urls import patterns, include, url
from ffos.recommender.rlogging.views import goto
from tastypie.api import Api
from ffos.recommender.tp_api import RecommendationResource
v1_api = Api(api_name='v1')
v1_api.register(RecommendationResource())

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'source.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r"^go/$", goto, name="click_app"),
    url(r'^', include('ffos.gui.urls')),
    url(r'^api/v2/', include("ffos.recommender.api.urls")),
    url(r'^api/', include(v1_api.urls)),
    url(r'^api/recommendation/', include('ffos.recommender.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
