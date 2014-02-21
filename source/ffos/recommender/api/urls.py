# -*- coding: utf-8 -*-
"""
.. module:: ffos.recommender.api.urls
    :platform: Unix, Windows
    :synopsis: 
     2/19/14

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from django.conf.urls import patterns, url

import views

urlpatterns = patterns("",
    url(r'^(?P<source>\b(%(source)s)\b)/(?P<user_external_id>\w+)/(?P<item_external_id>\w+)/$' % {"source":
    "|".join(views.GoToItemStore.source_types)},
        views.GoToItemStore().as_view(), name='go_to_store'),
    url(r'^recommend/(?P<number_of_recommendations>[0-9]+)/(?P<user_external_id>\w[\w/-]*)/(?P<data_format>\w+)/$',
        views.UserRecommendationAPI().as_view(), name='recommender_api'),
    url(r'^recommend/(?P<number_of_recommendations>[0-9]+)/(?P<user_external_id>\w[\w/-]*)/$',
        views.UserRecommendationAPI().as_view(), name='recommender_no_format_api'),
    url(r'^recommend/(?P<number_of_recommendations>[0-9]+)/(?P<user_external_id>\w[\w/-]*).(?P<data_format>\w+)$',
        views.UserRecommendationAPI().as_view(), name='recommender_file_api'),
    url(r'^item/(?P<item_external_id>[0-9]+)/(?P<data_format>\w+)/$', views.ItemAPI().as_view(), name='item_api'),
    url(r'^item/(?P<item_external_id>[0-9]+)/$', views.ItemAPI().as_view(), name='item_no_format_api'),
    url(r'^item/(?P<item_external_id>[0-9]+).(?P<data_format>\w+)$', views.ItemAPI().as_view(), name='item_file_api'),
    url(r'^user-items/(?P<user_external_id>\w[\w/-]*)/(?P<data_format>\w+)/$', views.UserItemsAPI().as_view(),
        name='user_item_api'),
    url(r'^user-items/(?P<user_external_id>\w[\w/-]*)/$', views.UserItemsAPI().as_view(),
        name='user_no_format_api'),
    url(r'^user-items/(?P<user_external_id>\w[\w/-]*).(?P<data_format>\w+)$', views.UserItemsAPI().as_view(),
        name='user_items_file_api'),
)