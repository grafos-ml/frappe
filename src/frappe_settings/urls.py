from django.conf.urls import patterns, include, url

#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mozzila.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    
    url(r"^api/v2/", include("recommendation.api.urls")),
    #url(r'^admin/', include(admin.site.urls)),
)
