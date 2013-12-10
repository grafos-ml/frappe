'''
Url for recommendation API


'''
from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^$',views.Landing.as_view(),
        name='recommendation_index'),
    url(r'^users/(?P<page>\d+)/$',views.Landing.as_view(),
        name='recommendation_landing'),
)