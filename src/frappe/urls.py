#! -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns(
    "",
    url(r"^health", include("health_check.urls")),
    url(r"^api/v2/", include("frappe.api.urls")),
    url(r"^admin/", include(admin.site.urls))
)
