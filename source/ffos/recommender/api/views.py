# -*- coding: utf-8 -*-

"""
.. module:: ffos.recommender.api.views
    :platform: Unix, Windows
    :synopsis: The views for the Recommend API.
     Created at Fev 19, 2014

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
"""
__author__ = "joaonrb"

from django.conf import settings
from django.db import connection
from django.db.utils import OperationalError
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from rest_framework.renderers import JSONRenderer, XMLRenderer
from rest_framework.parsers import JSONParser, XMLParser
from rest_framework.views import APIView
from ffos.recommender.controller import SimpleController
from ffos.recommender.rlogging.rerankers import SimpleLogReRanker
from ffos.models import FFOSApp, FFOSUser
from ffos.recommender.rlogging.models import RLog

import warnings

JSON = "json"
XML = "xml"
DEFAULT_FORMAT = JSON
ALLOWED_FORMATS = (JSON, XML)

FORMAT = lambda data_format: {
    JSON: (JSONParser, JSONResponse),
    XML: (XMLParser, XMLResponse)
}[data_format]

SUCCESS = 200
SUCCESS_MESSAGE = {
    _("status"): SUCCESS,
    _("message"): _("Done.")
}

FORMAT_ERROR = 400
FORMAT_ERROR_MESSAGE = {
    _("status"): FORMAT_ERROR,
    _("error"): _("Format chosen is not allowed. Allowed format %s.") % ", ".join(ALLOWED_FORMATS)
}

PARAMETERS_IN_MISS = {
    _("status"): FORMAT_ERROR,
    _("error"): _("Some parameters are missing. Check documentation.")
}

NOT_FOUND_ERROR = 404

RECOMMENDER = SimpleController()
RECOMMENDER.registerReranker(SimpleLogReRanker())


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
    content_type = "application/xml"
    renderer = XMLRenderer()


class RecommendationAPI(APIView):
    """
    .. py:class:: ffos.recommender.api.views.RecommendationAPI()


    About
    -----

    An "abstract kind" of view class that implements a APIView from rest_framework
    """
    format_parser = None
    format_response = None

    def dispatch(self, request, data_format=JSON, *args, **kwargs):
        """
        Check the format of the request/response by the argument

        :param request: Django HTTP request
        :type request: HTTPRequest
        :param data_format: The data format of the request/response. Must be something in "json", "xml",...
        :type data_format: str
        :param args: Generic extra anonymous parameters
        :param kwargs: Generic key words parameters
        """
        try:
            self.format_parser, self.format_response = FORMAT(data_format)
        except KeyError:
            return FORMAT(DEFAULT_FORMAT)[1](FORMAT_ERROR_MESSAGE, status=FORMAT_ERROR)
        return super(RecommendationAPI, self).dispatch(request, *args, **kwargs)


class GoToItemStore(APIView):
    """
    .. py:class:: ffos.recommender.api.views.GoToItemStore()

    About
    -----

    Goes to the store
    """

    http_method_names = [
        'get',
        #'post',
        #'put',
        #'patch',
        #'delete',
        #'head',
        #'options',
        #'trace'
    ]

    RECOMMENDED = "recommended"
    STANDARD = "standard"
    ANONYMOUS = "anonymous"
    source_types = [RECOMMENDED, STANDARD]
    source_map = {
        RECOMMENDED: RLog.CLICK_RECOMMENDED,
        STANDARD: RLog.CLICK
    }

    def click(self, user, item, click_type, rank=None):
        """
        Click on an app.

        :param user: User external_id that do the click.
        :type user: str or None
        :param item: Item external_id that is clicked.
        :type item: str
        :param click_type: The type of click that is.
        :type click_type: str
        :param rank: Rank of the item on recommendation. Default=None.
        :type rank: int
        """
        warnings.warn("This insert was only tested for MySQL", Warning)
        query = \
            ("""
             INSERT INTO %(database)s.rlogging_rlog
                SELECT NULL, ffos_ffosuser.id, ffos_ffosapp.id, NOW(), %(rank)s, %(type)s
                FROM %(database)s.ffos_ffosuser, %(database)s.ffos_ffosapp
                WHERE %(database)s.ffos_ffosuser.external_id="%(user)s"
                AND %(database)s.ffos_ffosapp.external_id="%(item)s";
             """ if user else
             """
             INSERT INTO %(database)s.rlogging_rlog
                SELECT NULL, NULL, ffos_ffosapp.id, NOW(), %(rank)s, %(type)s
                FROM %(database)s.ffos_ffosuser, %(database)s.ffos_ffosapp
                AND %(database)s.ffos_ffosapp.external_id="%(item)s";
             """) % \
            {
                "database": settings.DATABASES["default"]["NAME"],
                "user": user,
                "item": item,
                "type": self.source_map[click_type],
                "rank": rank or "NULL"
            }
        cursor = connection.cursor()
        a = cursor.execute(query)
        if a == 0:
            raise OperationalError("RLog not inserted")

    def get(self, request, user_external_id, item_external_id, source):
        """
        The go to store get request

        :param request: Django HTTP request
        :type request: HTTPRequest
        :param user_external_id: The external id of the user making the click or anonymous
        :type user_external_id: str
        :param item_external_id: The external id of the item clicked
        :type item_external_id: str
        :param source: The source of the click. If is standard or from a recommendation. If is originated from a
        recommendation, than it must have a GET parameter called ´´rank´´
        :type source: str
        """
        rank = request.GET.get("rank", None)
        if (source not in self.source_types) or (not rank and source == self.RECOMMENDED):
            raise Http404
        user = get_object_or_404(FFOSUser, external_id=user_external_id)
        app = get_object_or_404(FFOSApp, external_id=item_external_id)
        if source in self.source_types[:-1]:
            RLog.objects.create(user=user, item=app, type=self.source_map[source], value=rank)
        return HttpResponseRedirect(app.store_url)


class UserRecommendationAPI(RecommendationAPI):
    """
    .. py:class:: ffos.recommender.api.views.UserRecommendationAPI()

    About
    -----

    A class based view for the recommendation. This View ony support the get method
    """

    http_method_names = [
        'get',
        #'post',
        #'put',
        #'patch',
        #'delete',
        #'head',
        #'options',
        #'trace'
    ]

    def get(self, _, user_external_id, number_of_recommendations):
        """
        The get method
        """
        recommended_apps = RECOMMENDER.get_external_id_recommendations(user_external_id,
                                                                       n=int(number_of_recommendations))
        data = {"user": user_external_id, "recommendations": recommended_apps}
        return self.format_response(data)


class ItemAPI(RecommendationAPI):
    """
    ... py:class:: ffos.recommender.api.views.ItemAPI()

    About
    -----

    Class to check detail of items.
    """

    http_method_names = [
        'get',
        #'post',
        #'put',
        #'patch',
        #'delete',
        #'head',
        #'options',
        #'trace'
    ]

    NOT_FOUND_ERROR_MESSAGE = {
        _("status"): NOT_FOUND_ERROR,
        _("error"): _("Item with that id has not found.")
    }

    def get(self, request, app_external_id):
        """
        The get method
        """
        user = request.GET.get("user", None)
        try:
            app = FFOSApp.objects.filter(external_id=app_external_id).values("external_id", "name", "icon__size64",
                                                                             "icon__size16", "slug", "id")[0]
            user = FFOSUser.objects.filter(external_id=user).values("id")[0]["id"] if user else None
        except FFOSApp.DoesNotExist:
            return self.format_response(self.NOT_FOUND_ERROR_MESSAGE, status=NOT_FOUND_ERROR)

        source = bool(request.GET.get("source", None))
        if user and source == "recommendation":
            RLog.objects.create(user=user, item=app["id"], type=RLog.CLICK_RECOMMENDED)
        response = {"external_id": app["external_id"], "name": app["name"], "icon": app["icon__size64"],
                    "icon_small": app["icon__size16"]}
        return self.format_response(response)


class UserItemsAPI(RecommendationAPI):
    """
    ... py:class:: ffos.recommender.api.views.AcquireItemAPI()

    About
    -----

    This API allows a user to check upon their acquired items, to acquire a new item and to drop an old one.
    """

    NOT_FOUND_ERROR_MESSAGE = {
        _("status"): NOT_FOUND_ERROR,
        _("error"): _("User with that id has not found.")
    }

    http_method_names = [
        'get',
        'post',
        #'put',
        #'patch',
        'delete',
        #'head',
        #'options',
        #'trace'
    ]

    @staticmethod
    def insert_acquisition(user, item):
        """
        Insert a new
        """
        warnings.warn("This insert was only tested for MySQL", Warning)
        query = \
            """
            INSERT INTO %(database)s.ffos_installation
                SELECT NULL, ffos_ffosuser.id, ffos_ffosapp.id, NOW(), NULL
                FROM %(database)s.ffos_ffosuser, %(database)s.ffos_ffosapp
                WHERE %(database)s.ffos_ffosuser.external_id="%(user)s"
                AND %(database)s.ffos_ffosapp.external_id="%(item)s";
            """ % {
                "database": settings.DATABASES["default"]["NAME"],
                "user": user,
                "item": item}
        cursor = connection.cursor()
        a = cursor.execute(query)
        if a == 0:
            raise OperationalError("Item not inserted")

    @staticmethod
    def delete_acquisition(user, item):
        """
        Insert a new
        """
        warnings.warn("This insert was only tested for MySQL", Warning)
        query = \
            """
            UPDATE %(database)s.ffos_installation, %(database)s.ffos_ffosuser, %(database)s.ffos_ffosapp
                SET %(database)s.ffos_installation.removed_date=NOW()
                WHERE %(database)s.ffos_ffosapp.external_id="%(item)s"
                AND %(database)s.ffos_ffosuser.external_id="%(user)s"
                AND %(database)s.ffos_installation.user_id=%(database)s.ffos_ffosuser.id
                AND %(database)s.ffos_installation.app_id=%(database)s.ffos_ffosapp.id;
            """ % {
                "database": settings.DATABASES["default"]["NAME"],
                "user": user,
                "item": item}
        cursor = connection.cursor()
        a = cursor.execute(query)
        if a == 0:
            raise OperationalError("Item not deleted")

    def get(self, request, user_external_id):
        """
        Get method. It may receive get parameters
        """
        offset = request.GET.get("offset", 0)  # Offset of items
        items = request.GET.get("items", 20)  # Number of items to present
        try:
            apps = FFOSUser.objects.get(external_id=user_external_id).installed_apps.all()
            apps = [int(app) for app, in apps[offset:items].values_list("external_id")]
        except FFOSUser.DoesNotExist:
            return self.format_response(self.NOT_FOUND_ERROR_MESSAGE, status=NOT_FOUND_ERROR)
        data = {"user": user_external_id, "installed": apps}
        return self.format_response(data)

    def post(self, request, user_external_id):
        """
        Post method
        """
        try:
            item_id = request.POST["item_to_acquire"]
        except KeyError:
            return self.format_response(PARAMETERS_IN_MISS, status=FORMAT_ERROR)

        #Installation.objects.create(user_id=FFOSUser.objects.get(external_id=user_external_id).pk,
        #                            app_id=FFOSApp.objects.get(external_id=item_id).pk,
        #                            installation_date=timezone.now())
        self.insert_acquisition(user_external_id, item_id)
        return self.format_response(SUCCESS_MESSAGE)

    def delete(self, request, user_external_id):
        """
        Delete Rest method to remove items from user stack
        """
        try:
            item_id = request.DATA["item_to_acquire"]
        except KeyError:
            return self.format_response(PARAMETERS_IN_MISS, status=FORMAT_ERROR)

        self.delete_acquisition(user_external_id, item_id)
        return self.format_response(SUCCESS_MESSAGE)