'''
Url for recommendation API


'''
from django.conf.urls import patterns, url
from django.contrib import admin
admin.autodiscover()

import views

urlpatterns = patterns('',
    url(r'^',views.RecomenderAPI.as_view(),
        name='recommender_request'),
)