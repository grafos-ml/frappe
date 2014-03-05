# -*- coding: utf-8 -*-
"""
Created at February 19, 2014

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from django.conf.urls import patterns, url
from firefox.api import views

urlpatterns = patterns("",
    url(r'^(?P<source>\b(%(source)s)\b)/(?P<user_external_id>\w+)/(?P<item_external_id>\w+)/$' % {"source":
    "|".join(views.GoToItem.source_types)},
        views.GoToItem().as_view(), name='go_to_store'),
    url(r'^item/(?P<item_external_id>[0-9]+)/(?P<data_format>\w+)/$', views.ItemAPI().as_view(), name='item_api'),
    url(r'^item/(?P<item_external_id>[0-9]+)/$', views.ItemAPI().as_view(), name='item_no_format_api'),
    url(r'^item/(?P<item_external_id>[0-9]+).(?P<data_format>\w+)$', views.ItemAPI().as_view(), name='item_file_api'),
)