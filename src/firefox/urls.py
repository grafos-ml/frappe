# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = \
    patterns('',
             url(r'^', include('firefox.gui.urls')),
             url(r'^api/v2/', include("recommendation.api.urls")),
             url(r'^api/v2/', include("firefox.api.urls")),
             url(r'^admin/', include(admin.site.urls)),
)
