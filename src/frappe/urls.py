#! -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from health_check.plugins import plugin_dir
from frappe.backends import CheckDefaultCacheBackend, CheckOwnedItemsCacheBackend
from django.contrib import admin
admin.autodiscover()

plugin_dir.register(CheckDefaultCacheBackend)
plugin_dir.register(CheckOwnedItemsCacheBackend)

urlpatterns = patterns(
    "",
    url(r"^health", include("health_check.urls")),
    url(r"^api/v2/", include("frappe.api.urls")),
    url(r"^admin/", include(admin.site.urls))
)
