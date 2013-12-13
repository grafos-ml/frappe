'''
Url for recommendation API


'''
from django.conf.urls import patterns, url
from django.views.decorators.cache import cache_page
from ffos.recommender.caches import CacheUser
import views

urlpatterns = patterns('',
    url(r'^$',cache_page(15*60)(views.Landing.as_view()),
        name='recommendation_index'),
    url(r'^users/(?P<page>\d+)/$',cache_page(15*60)(views.Landing.as_view()),
        name='recommendation_landing'),
    url(r'^recommendfor/(?P<user>[\S]*)/$',CacheUser.decorator(
        views.Recommend.as_view()),name='recommendfor'),
)