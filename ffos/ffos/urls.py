from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'ffos.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^',include('ffos.gui.urls')),
    url(r'^api/recommendation/',include('ffos.recommender.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
