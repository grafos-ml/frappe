# -*- coding: utf-8 -*-

"""
Version 3
Created at Nov 4, 2014

The views for the Recommend API.
"""

__author__ = "joaonrb"

from django.http import HttpResponse
from django.views.generic.base import View
from rest_framework.renderers import JSONRenderer
from frappe.models import Module, User


class RecommendationAPI(View):
    """
    A class based view for the recommendation. This View ony support the get method
    """
    json_renderer = JSONRenderer()
    render_to_json = \
        lambda self, data: HttpResponse(RecommendationAPI.json_renderer.render(data), content_type="application/json")
    http_method_names = [
        "get"
    ]

    def get(self, request, user_eid, recommendation_size=5):
        """
        Get method to request recommendations

        :param request: This is the request. It is not needed but has to be here because of the django interface with
        views.
        :param user_eid: The user that want the recommendation ore the object of the recommendations.
        :param recommendation_size: Number of recommendations that are requested.
        :return: A HTTP response with a list of recommendations.
        """

        # Here is the decorator for recommendation
        recommendation = Module.pick_module(user_eid).predict_scores(User.get_user_by_external_id(user_eid),
                                                                     int(recommendation_size))
        return self.render_to_json({"user": user_eid, "recommendations": recommendation})