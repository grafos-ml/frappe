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
from django.core.urlresolvers import reverse
from rest_framework.renderers import JSONRenderer, XMLRenderer
from rest_framework.parsers import JSONParser, XMLParser
from rest_framework.views import APIView
from recommender.core import Recommender
from recommender.records.rerankers import SimpleLogReRanker
from ffos.models import FFOSApp, FFOSUser, Installation
from ffos.recommender.rlogging.models import RLog
from ffos.recommender.diversification import DiversityReRanker

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
NOT_FOUND_ERROR = 404

FORMAT_ERROR_MESSAGE = {
    _("status"): FORMAT_ERROR,
    _("error"): _("Format chosen is not allowed. Allowed format %s.") % ", ".join(ALLOWED_FORMATS)
}

PARAMETERS_IN_MISS = {
    _("status"): FORMAT_ERROR,
    _("error"): _("Some parameters are missing. Check documentation.")
}

RECOMMENDER = SimpleController()
RECOMMENDER.registerReranker(
    SimpleLogReRanker(),
    DiversityReRanker()
)


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
        :return: A JSON or XML or whatever is configured and asked by the client response
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
    CLICK = "click"
    ANONYMOUS = "anonymous"
    source_types = [RECOMMENDED, CLICK]
    source_map = {
        RECOMMENDED: RLog.CLICK_RECOMMENDED,
        CLICK: RLog.CLICK
    }

    def click(self, user_external_id, item_external_id, click_type, rank=None):
        """
        Click on an app.

        :param user_external_id: User external_id that do the click.
        :type user_external_id: str or None
        :param item_external_id: Item external_id that is clicked.
        :type item_external_id: str
        :param click_type: The type of click that is.
        :type click_type: str
        :param rank: Rank of the item on recommendation. Default=None.
        :type rank: int
        :raise OperationalError: When some of the data maybe wrongly inserted into data base
        """
        warnings.warn("This insert was only tested for MySQL", Warning)
        query = \
            ("INSERT INTO %(database)s.rlogging_rlog (id, user_id, item_id, timestamp, value, type)"
             "VALUES (NULL, %(user)s, \"%(item)s\", NOW(), %(rank)s, %(type)s);") % \
            {
                "database": settings.DATABASES["default"]["NAME"],
                "user": ('"%s"' % user_external_id) if user_external_id else "NULL",
                "item": item_external_id,
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
        :return: A HTTP response to redirect to the store item page.
        """
        rank = request.GET.get("rank", None)
        if (source not in self.source_types) or (not rank and source == self.RECOMMENDED):
            raise Http404
        user_external_id = user_external_id if user_external_id != self.ANONYMOUS else None
        self.click(user_external_id, item_external_id, source, rank)
        slug = FFOSApp.objects.filter(external_id=item_external_id).values_list("slug")[0]
        return HttpResponseRedirect(FFOSApp.slug_to_store_url(slug))


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
        Get method to request recommendations

        :param _: This is the request. It is not needed but has to be here because of the django interface with views.
        :param user_external_id: The user that want the recommendation ore the object of the recommendations.
        :type user_external_id: str
        :param number_of_recommendations: Number of recommendations that are requested.
        :type number_of_recommendations: int
        :return: A HTTP response with a list of recommendations.
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

    ITEM_EXPOSED_ATTRIBUTES = ["external_id", "name", "icon__size128", "icon__size64", "icon__size16", "slug", "id"]

    def get(self, request, item_external_id):
        """
        Get item details.

        :param request: The HTTP request
        :param item_external_id: The item external id that the details should be send.
        :type item_external_id: str
        :return: A HTTP response with the item information
        """
        try:
            app = FFOSApp.objects.filter(external_id=item_external_id).values(*self.ITEM_EXPOSED_ATTRIBUTES)[0]
        except FFOSApp.DoesNotExist:
            return self.format_response(self.NOT_FOUND_ERROR_MESSAGE, status=NOT_FOUND_ERROR)

        rank = request.GET.get("rank", None)
        uri = reverse("go_to_store", kwargs={
            "user_external_id": request.GET.get("user", GoToItemStore.ANONYMOUS),
            "item_external_id": item_external_id,
            "source": GoToItemStore.RECOMMENDED if rank else GoToItemStore.CLICK})
        if rank:
            uri += "?rank=%s" % rank
        response = {"external_id": app["external_id"], "name": app["name"], "icon": app["icon__size64"],
                    "icon_small": app["icon__size16"], "icon_large": app["icon__size128"], "store": uri}

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
    def insert_acquisition(user_external_id, item_external_id):
        """
        Insert a new in user installed apps

        :param user_external_id: The user external id.
        :type user_external_id: str
        :param item_external_id: The item external id.
        :type item_external_id: str
        :raise OperationalError: When some of the data maybe wrongly inserted into data base
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
            "user": user_external_id,
            "item": item_external_id}
        cursor = connection.cursor()
        a = cursor.execute(query)
        if a == 0:
            raise OperationalError("Item not inserted")

    @staticmethod
    def delete_acquisition(user_external_id, item_external_id):
        """
        Update a certain item to remove in the uninstall datetime field

        param user_external_id: The user external id.
        :type user_external_id: str
        :param item_external_id: The item external id.
        :type item_external_id: str
        :raise OperationalError: When some of the data maybe wrongly inserted into data base
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
            "user": user_external_id,
            "item": item_external_id}
        cursor = connection.cursor()
        a = cursor.execute(query)
        if a == 0:
            raise OperationalError("Item not deleted")

    def get(self, request, user_external_id):
        """
        Get the users owned items. It receives an extra set of GET parameters. The offset and the items.

        The ´´offset´´ represents the amount of items to pass before start sending results.
        The ´´items´´ represents the amount of items to show.

        :param request: The HTTP request.
        :param user_external_id: The user external id that are making the request.
        :type user_external_id: str
        :return: A list of app external ids of the user installed apps (apps that are in database with reference to this
         user and the removed date set to null).
        """
        offset = int(request.GET.get("offset", 0))  # Offset of items
        items = int(request.GET.get("items", 20))  # Number of items to present
        try:
            apps = Installation.objects.filter(user__external_id=user_external_id)
            apps = apps.order_by("installation_date")
            apps = apps.values_list("app__external_id", "installation_date", "removed_date")[offset:offset+items]
            apps = [{"external_id": int(app), "installation_date": date, "removed_date": removed_date}
                    for app, date, removed_date in apps]
        except FFOSUser.DoesNotExist:
            return self.format_response(self.NOT_FOUND_ERROR_MESSAGE, status=NOT_FOUND_ERROR)
        data = {"user": user_external_id, "applications": apps}
        return self.format_response(data)

    def post(self, request, user_external_id):
        """
        Puts a new item in the user installed apps. It should have a special POST parameter (besides the csrf token or
        other token needed to the connection) that is item_to_acquire.

        The ´´item_to_acquire´´ is the item external id that is supposed to be installed in the user inventory.

        :param request: The HTTP request.
        :param user_external_id: The user external id that are making the request.
        :type user_external_id: str
        :return: A success response if the input was successful =p
        """
        try:
            item_id = request.POST["item_to_acquire"]
        except KeyError:
            return self.format_response(PARAMETERS_IN_MISS, status=FORMAT_ERROR)

        self.insert_acquisition(user_external_id, item_id)
        return self.format_response(SUCCESS_MESSAGE)

    def delete(self, request, user_external_id):
        """
        removes an old item in the user installed apps. It should have a special POST parameter (besides the csrf token
        or other token needed to the connection) that is item_to_acquire.

        The ´´item_to_remove´´ is the item external id that is supposed to be removed in the user inventory.

        :param request: The HTTP request.
        :param user_external_id: The user external id that are making the request.
        :type user_external_id: str
        :return: A success response if the input was successful =p
        """
        try:
            item_id = request.DATA["item_to_remove"]
        except KeyError:
            return self.format_response(PARAMETERS_IN_MISS, status=FORMAT_ERROR)

        self.delete_acquisition(user_external_id, item_id)
        return self.format_response(SUCCESS_MESSAGE)