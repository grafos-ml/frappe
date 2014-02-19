# -*- coding: utf-8 -*-
"""
.. module:: ffos.recommender.api.urls
    :platform: Unix, Windows
    :synopsis: 
     2/19/14

.. moduleauthor:: joaonrb <>

"""
__author__ = "joaonrb"

from django.conf.urls import patterns, url

import views

urlpatterns = patterns("",
    url(r'^recommend/(?P<number_of_recommendations>[0-9]+)/(?P<user_external_id>\w[\w/-]*).(?P<data_format>\w+)$',
        views.UserRecommendationAPI().as_view(), name='recommender_request'),
)