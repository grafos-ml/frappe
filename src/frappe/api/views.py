# -*- coding: utf-8 -*-

"""
Version 3
Created at Nov 4, 2014

The views for the Recommend API.
"""

from __future__ import division, absolute_import, print_function
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.renderers import JSONRenderer
from rest_framework.negotiation import BaseContentNegotiation
from frappe.models import User
from frappe.core import RecommendationCore as Core
from frappe.tools.logger.loggers import DBLogger, NoLogging
from frappe.api.serializers import UserSerializer

__author__ = "joaonrb"


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

    @staticmethod
    def get(request, user_eid, recommendation_size=5):
        """
        Get method to request recommendations

        :param request: This is the request. It is not needed but has to be here because of the django interface with
        views.
        :param user_eid: The user that want the recommendation ore the object of the recommendations.
        :param recommendation_size: Number of recommendations that are requested.
        :return: A HTTP response with a list of recommendations.
        """
        logger = NoLogging if "nolog" in request.GET else DBLogger

        module = Core.pick_module(user_eid)
        user = User.get_user(user_eid)
        recommendation = module.predict_scores(user, int(recommendation_size))
        logger.recommendation(module, user, recommendation)
        return Response({"user": user_eid, "recommendations": recommendation})


class UserListAPI(ListAPIView):
    """
    Api for list users in system
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    paginate_by = 20
    paginate_by_param = "page_size"
    max_paginate_by = 100

    renderer_classes = [JSONRenderer]
    http_method_names = [
        "get",
    ]
    content_negotiation_class = IgnoreClientContentNegotiation
