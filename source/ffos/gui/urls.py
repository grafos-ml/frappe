'''
Url for recommendation API


'''
from django.conf.urls import patterns, url
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from ffos.recommender.caches import CacheUser
import views

urlpatterns = patterns('',
    url(r'^$',login_required(cache_page(15*60)(views.Landing.as_view()),
        login_url='/admin/'),name='recommendation_index'),
    url(r'^users/(?P<page>\d+)/$',login_required(cache_page(15*60)(
        views.Landing.as_view()),login_url='/admin/'),
        name='recommendation_landing'),
    url(r'^recommendfor/(?P<user>[\S]*)/$',login_required(CacheUser.decorator(
        views.Recommend.as_view()),login_url='/admin/'),name='recommendfor'),
)