__author__ = 'joaonrb'

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.views.generic import TemplateView
from recommendation.api.views import JSONResponse
from recommendation.ab_testing.models import Experiment, Event
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

'''
class ABPopulationStats(APIView):
    """
    View for population statistics
    """
    http_method_names = [
        "get"
    ]

    def get(self, request, version=None):
        """
        Get the population statistics like the number of A or B test results so far
        """
        kwargs = {}
        if version:
            kwargs["version"] = get_object_or_404(ABVersion, pk=version)
        else:
            kwargs["version"] = ABVersion.cached_version
        try:
            kwargs["timestamp__gt"] = request.GET.get("starting")
        except KeyError:
            pass
        try:
            kwargs["timestamp__lt"] = request.GET.get("ending")
        except KeyError:
            pass
        events = ABEvent.objects.filter(**kwargs)
        results = {}
        for event in events:
            try:
                r = results[event.model]
            except KeyError:
                results[event.model] = r = {"count"}
'''


class ABEventsAPI(APIView):
    """
    View for event list
    """
    http_method_names = [
        "get"
    ]

    def get(self, request, version=None):
        kwargs = {}
        if version:
            kwargs["experiment"] = get_object_or_404(Experiment, pk=version)
        else:
            kwargs["experiment"] = Experiment.cached_version()
        print Experiment.cached_version()
        if not kwargs["experiment"]:
            return JSONResponse({"message": "No ab-test started", "code": 404}, status=404)
        try:
            kwargs["timestamp__gt"] = request.GET["starting"]
        except KeyError:
            pass
        try:
            kwargs["timestamp__lt"] = request.GET["ending"]
        except KeyError:
            pass
        print kwargs
        events = Event.objects.filter(**kwargs).values("model", "timestamp", "experiment", "type", "value",
                                                         "user__external_id", "item__external_id")
        return JSONResponse(events)


class ABDashboardView(TemplateView):
    """

    """
    http_method_names = [
        "get"
    ]
    template_name = "ab_testing/dashboard.jade"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ABDashboardView, self).dispatch(*args, **kwargs)


