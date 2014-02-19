# -*- coding: utf-8 -*-
"""
.. module:: ffos.recommender.api.views
    :platform: Unix, Windows
    :synopsis: The views for the Recommend API.
     Created at Fev 19, 2014

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer, XMLRenderer
from rest_framework.parsers import JSONParser, XMLParser
from rest_framework.views import APIView
from ffos.recommender.controller import SimpleController
from ffos.recommender.rlogging.rerankers import SimpleLogReRanker
from ffos.recommender.api.serializers import ItemRecommendedSerializer

JSON = "json"
XML = "xml"
DEFAULT_FORMAT = JSON

FORMAT = lambda data_format: {
    JSON: (JSONParser, JSONResponse),
    XML: (XMLParser, XMLResponse)
}[data_format]

FORMAT_ERROR = 400
FORMAT_ERROR_MESSAGE = {
    _("status"): FORMAT_ERROR,
    _("error"): _("Format chosen is not allowed. Allowed format %s.") % ", ".join(FORMAT.keys())
}

RECOMMENDER = SimpleController()
RECOMMENDER.registerFilter(SimpleLogReRanker)


class APIResponse(HttpResponse):
    """
    .. py:class:: ffos.recommender.api.views.APIResponse(data)


    About
    -----

    A abstract HttpResponse that renders its content for the API.
    """
    content_type = None
    renderer = None

    def __init__(self, data, **kwargs):
        content = self.renderer.render(data)
        kwargs['content_type'] = self.content_type
        super(APIResponse, self).__init__(content, **kwargs)


class JSONResponse(APIResponse):
    """
    .. py:class:: ffos.recommender.api.views.JSONResponse(data)


    About
    -----

    A HttpResponse that renders its content into JSON.
    """
    content_type = "application/json"
    renderer = JSONRenderer()


class XMLResponse(APIResponse):
    """
    .. py:class:: ffos.recommender.api.views.XMLResponse(data)


    About
    -----

    A HttpResponse that renders its content into XML.
    """
    content_type = "text/xml"
    renderer = XMLRenderer()


class UserRecommendation(APIView):
    """
    .. py:class:: ffos.recommender.api.views.UserRecommendation()

    About
    -----

    A class based view for the recommendation. This View ony support the get method
    """

    def get(self, request, user_external_id, number_of_recommendations, data_format=JSON):
        """
        The get method
        """
        recommended_apps = RECOMMENDER.get_recommendations_items(user_external_id, n=number_of_recommendations)
        serializer = ItemRecommendedSerializer(recommended_apps, many=True)
        try:
            return FORMAT(data_format)[1](serializer.data)
        except KeyError:
            return FORMAT(DEFAULT_FORMAT)[1](FORMAT_ERROR_MESSAGE, status=FORMAT_ERROR)