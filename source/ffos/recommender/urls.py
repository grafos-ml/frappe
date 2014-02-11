"""
Url for recommendation API


"""
from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^', views.RecomenderAPI.as_view(), name='recommender_request'),
)