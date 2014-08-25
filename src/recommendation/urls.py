# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    "",
    url(r"^api/", include("recommendation.api.urls")),
    url(r"^admin/", include(admin.site.urls))
)
