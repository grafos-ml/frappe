'''
Url for recommendation API


'''
from django.conf.urls import patterns, url
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login, logout
from django.core.urlresolvers import reverse
from ffos.recommender.caches import CacheUser
import views

urlpatterns = patterns('',
    url(r'^$',login_required(cache_page(15*60)(views.Landing.as_view()),
        login_url=reverse('login')),name='recommendation_index'),
    url(r'^users/(?P<page>\d+)/$',login_required(cache_page(15*60)(
        views.Landing.as_view()),login_url=reverse('login')),
        name='recommendation_landing'),
    url(r'^recommendfor/(?P<user>[\S]*)/$',login_required(CacheUser.decorator(
        views.Recommend.as_view()),login_url=reverse('login')),name='recommendfor'),
    url(r'^login/$',login,template_name='login.html',name='login'),
    url(r'^logout/$',logout,name='logout'),
)