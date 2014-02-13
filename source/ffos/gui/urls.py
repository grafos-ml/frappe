'''
Url for recommendation API


'''
from django.conf.urls import patterns, url
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout
from ffos.recommender.caches import CacheUser
import views

urlpatterns = patterns('',
    url(r'^$',login_required(cache_page(15*60)(views.Landing.as_view())), name='recommendation_index'),
    url(r'^users/(?P<page>\d+)/$',login_required(cache_page(15*60)(views.Landing.as_view())),
        name='recommendation_landing'),
    url(r'^recommendfor/(?P<user>[\S]*)/$',login_required(CacheUser()(views.Recommend.as_view())),name='recommendfor'),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    url(r'^accounts/logout/$',logout,name='logout'),
)