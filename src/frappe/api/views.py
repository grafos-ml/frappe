# -*- coding: utf-8 -*-

"""
Version 3
Created at Nov 4, 2014

The views for the Recommend API.
"""

__author__ = "joaonrb"

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework.negotiation import BaseContentNegotiation
from frappe.models import User
from frappe.core import RecommendationCore as core


class IgnoreClientContentNegotiation(BaseContentNegotiation):
    def select_parser(self, request, parsers):
        """
        Select the first parser in the `.parser_classes` list.
        """
        return parsers[0]

    def select_renderer(self, request, renderers, format_suffix=None):
        """
        Select the first renderer in the `.renderer_classes` list.
        """
        return renderers[0], renderers[0].media_type


class RecommendationAPI(APIView):
    """
    A class based view for the recommendation. This View ony support the get method
    """
    renderer_classes = [JSONRenderer]
    http_method_names = [
        "get"
    ]
    content_negotiation_class = IgnoreClientContentNegotiation

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
        recommendation = core.pick_module(user_eid).predict_scores(User.get_user_by_external_id(user_eid),
                                                                   int(recommendation_size))
        return Response({"user": user_eid, "recommendations": recommendation})