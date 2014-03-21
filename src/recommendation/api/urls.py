# -*- coding: utf-8 -*-
"""
.. module:: ffos.recommendation.api.urls
    :platform: Unix, Windows
    :synopsis: 
     2/19/14

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from django.conf.urls import patterns, url

from recommendation.api import views

urlpatterns = patterns("",
    url(r'^recommend/(?P<number_of_recommendations>[0-9]+)/(?P<user_external_id>\w[\w/-]*)/(?P<data_format>\w+)/$',
        views.UserRecommendationAPI().as_view(), name='recommender_api'),
    url(r'^recommend/(?P<number_of_recommendations>[0-9]+)/(?P<user_external_id>\w[\w/-]*)/$',
        views.UserRecommendationAPI().as_view(), name='recommender_no_format_api'),
    url(r'^recommend/(?P<number_of_recommendations>[0-9]+)/(?P<user_external_id>\w[\w/-]*).(?P<data_format>\w+)$',
        views.UserRecommendationAPI().as_view(), name='recommender_file_api'),
    url(r'^user-items/(?P<user_external_id>\w[\w/-]*)/(?P<data_format>\w+)/$', views.UserItemsAPI().as_view(),
        name='user_item_api'),
    url(r'^user-items/(?P<user_external_id>\w[\w/-]*)/$', views.UserItemsAPI().as_view(),
        name='user_no_format_api'),
    url(r'^user-items/(?P<user_external_id>\w[\w/-]*).(?P<data_format>\w+)$', views.UserItemsAPI().as_view(),
        name='user_items_file_api'),
)