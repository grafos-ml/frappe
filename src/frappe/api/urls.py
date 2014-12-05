#! -*- coding: utf-8 -*-
"""
.. module:: ffos.recommendation.api.urls
    :platform: Unix, Windows
    :synopsis: 
     2/19/14

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from django.conf.urls import patterns, url
from health_check.plugins import plugin_dir
from frappe.backends import CheckDefaultCacheBackend, CheckOwnedItemsCacheBackend, CheckModuleCacheBackend
from frappe.api import views

plugin_dir.register(CheckDefaultCacheBackend)
plugin_dir.register(CheckOwnedItemsCacheBackend)
plugin_dir.register(CheckModuleCacheBackend)

urlpatterns = patterns("",
    url(r"^recommend/(?P<recommendation_size>[0-9]+)/(?P<user_eid>\w[\w/-]*)/$", views.RecommendationAPI.as_view(),
        name="recommendation_api"),
    url(r"^click/$", views.ClickAPI.as_view(), name="click_api"),
    url(r"^users/$", views.UserListAPI.as_view(), name="users_api"),
    url(r"^user/(?P<user_eid>\w[\w/-]*)/$", views.UserItemsAPI.as_view(), name="user_items_api")
)