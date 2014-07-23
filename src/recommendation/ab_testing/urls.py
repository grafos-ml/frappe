from django.conf.urls import patterns, url
from recommendation.ab_testing import views

urlpatterns = \
    patterns("",
             url(r"^dashboard/$", views.ABDashboardView.as_view(), name="ab_dashboard"),
             url(r"^events/$", views.ABEventsAPI.as_view(), name="ab_events"),
             )