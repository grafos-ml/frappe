__author__ = 'joaonrb'

from django.conf.urls import patterns, url
from recommendation.testfm_results.views import AnalyzeModels

urlpatterns = patterns("", url(r"^$", AnalyzeModels.as_view()))