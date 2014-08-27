# -*- coding: utf-8 -*-

"""
Created at Fev 19, 2014

The views for the Recommend API.

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
"""
__author__ = "joaonrb"

import random
from django.conf import settings
from django.db import connection
from django.utils.timezone import now
from django.db.utils import OperationalError, IntegrityError
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from rest_framework.renderers import JSONRenderer, XMLRenderer
from rest_framework.parsers import JSONParser, XMLParser
from rest_framework.views import APIView
from recommendation.models import User, Inventory, Item
from recommendation.core import get_controller
from recommendation.decorators import GoToThreadQueue
from recommendation.core import log_event

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


class APIResponse(HttpResponse):
    """
    .. py:class:: recommendation.api.views.APIResponse(data)


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
    .. py:class:: recommendation.api.views.JSONResponse(data)


    About
    -----

    A HttpResponse that renders its content into JSON.
    """
    content_type = "application/json"
    renderer = JSONRenderer()


class XMLResponse(APIResponse):
    """
    .. py:class:: recommendation.api.views.XMLResponse(data)


    About
    -----

    A HttpResponse that renders its content into XML.
    """
    content_type = "application/xml"
    renderer = XMLRenderer()


class RecommendationAPI(APIView):
    """
    .. py:class:: recommendation.api.views.RecommendationAPI()


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


class AbstractGoToItem(APIView):
    """
    Abstract go to store to be implemented by the real item
    """

    RECOMMENDED = "recommended"
    CLICK = "click"
    ANONYMOUS = "anonymous"
    source_types = [RECOMMENDED, CLICK]
    source_map = {
        RECOMMENDED: log_event.RECOMMEND,
        CLICK: log_event.CLICK
    }

    @log_event(log_event.CLICK)
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
        #query = \
        #    ("INSERT INTO %(database)s.records_record (id, user_id, item_id, timestamp, value, type) "
        #     "VALUES (NULL, %(user)s, \"%(item)s\", NOW(), %(rank)s, %(type)s);") % \
        #    {
        #        "database": settings.DATABASES["default"]["NAME"],
        #        "user": ('"%s"' % user_external_id) if user_external_id else "NULL",
        #        "item": item_external_id,
        #        "type": self.source_map[click_type],
        #        "rank": rank or "NULL"
        #    }
        #cursor = connection.cursor()
        #a = cursor.execute(query)
        #if a == 0:
        #    raise OperationalError("Record not inserted")


class UserRecommendationAPI(RecommendationAPI):
    """
    .. py:class:: recommendation.api.views.UserRecommendationAPI()

    About
    -----

    A class based view for the recommendation. This View ony support the get method
    """

    http_method_names = [
        "get"
    ]

    def get(self, request, user_external_id="", number_of_recommendations=5):
        """
        Get method to request recommendations

        :param request: This is the request. It is not needed but has to be here because of the django interface with views.
        :param user_external_id: The user that want the recommendation ore the object of the recommendations.
        :type user_external_id: str
        :param number_of_recommendations: Number of recommendations that are requested.
        :type number_of_recommendations: int
        :return: A HTTP response with a list of recommendations.
        """
        if user_external_id == "":
            user = random.sample(User.user_by_external_id, 1)[0]
        else:
            user = User.user_by_external_id[user_external_id]
        recommended_apps = log_event(log_event.RECOMMEND)(
            get_controller().get_external_id_recommendations)(user, n=int(number_of_recommendations))
        data = {"user": user.external_id, "recommendations": recommended_apps}
        return self.format_response(data)


class UsersAPI(RecommendationAPI):
    """
    Class for API view of the users
    """

    NOT_FOUND_ERROR_MESSAGE = {
        _("status"): NOT_FOUND_ERROR,
        _("error"): _("User with that id has not found.")
    }

    EXTERNAL_ID_EXISTS_ERROR_MESSAGE = {
        _("status"): NOT_FOUND_ERROR,
        _("error"): _("User with that id already exists.")
    }

    http_method_names = [
        "get",
        "post",
    ]

    def get(self, request):
        """
        Return a list of users
        """
        offset = int(request.GET.get("offset", 0))
        number_of_users = int(request.GET.get("users", 0))
        users = User.objects.all()
        ordered_users = users.order_by("id")
        users_list = \
            ordered_users.values_list("id",
                                      "external_id")[offset:(offset+number_of_users) if number_of_users else None]
        return self.format_response([{"external_id": eid, "id": iid} for iid, eid in users_list])

    def post(self, request):
        """
        creates a new user
        """
        try:
            new_user_external_id = request.DATA.get("external_id")
        except KeyError:
            return self.format_response(PARAMETERS_IN_MISS, status=FORMAT_ERROR)
        try:
            User.objects.create(external_id=new_user_external_id)
        except IntegrityError:
            return self.format_response(self.EXTERNAL_ID_EXISTS_ERROR_MESSAGE, status=500)
        return self.format_response(SUCCESS_MESSAGE)


class UserItemsAPI(RecommendationAPI):
    """
    ... py:class:: recommendation.api.views.AcquireItemAPI()

    About
    -----

    This API allows a user to check upon their acquired items, to acquire a new item and to drop an old one.
    """

    NOT_FOUND_ERROR_MESSAGE = {
        _("status"): NOT_FOUND_ERROR,
        _("error"): _("User with that id has not found.")
    }

    http_method_names = [
        "get",
        "post",
        "delete"
    ]

    @staticmethod
    #@GoToThreadQueue()
    @log_event(log_event.ACQUIRE)
    def insert_acquisition(user_external_id, item_external_id):
        """
        Insert a new in user installed apps

        :param user_external_id: The user external id.
        :type user_external_id: str
        :param item_external_id: The item external id.
        :type item_external_id: str
        :raise OperationalError: When some of the data maybe wrongly inserted into data base
        """
        #query = \
        #    """
        #    INSERT INTO %(database)s.recommendation_inventory
        #        SELECT NULL, recommendation_user.id, recommendation_item.id, NOW(), NULL
        #        FROM %(database)s.recommendation_user, %(database)s.recommendation_item
        #        WHERE %(database)s.recommendation_user.external_id="%(user)s"
        #        AND %(database)s.recommendation_item.external_id="%(item)s";
        #    """ % {
        #    "database": settings.DATABASES["default"]["NAME"],
        #    "user": user_external_id,
        #    "item": item_external_id}
        #cursor = connection.cursor()
        #a = cursor.execute(query)
        #if a == 0:
        #    raise OperationalError("Item not inserted")
        ##########
        Inventory.objects.create(item=Item.item_by_external_id[item_external_id],
                                 user=User.user_by_external_id[user_external_id], acquisition_date=now())
        #User.user_by_external_id[user_external_id].items.add(Item.item_by_external_id[item_external_id])

    @staticmethod
    #@GoToThreadQueue()
    @log_event(log_event.REMOVE)
    def delete_acquisition(user_external_id, item_external_id):
        """
        Update a certain item to remove in the uninstall datetime field

        param user_external_id: The user external id.
        :type user_external_id: str
        :param item_external_id: The item external id.
        :type item_external_id: str
        :raise OperationalError: When some of the data maybe wrongly inserted into data base
        """
        #query = \
        #    """
        #    UPDATE %(database)s.recommendation_inventory, %(database)s.recommendation_user,
        #     %(database)s.recommendation_item
        #        SET %(database)s.recommendation_inventory.dropped_date=NOW()
        #        WHERE %(database)s.recommendation_item.external_id="%(item)s"
        #        AND %(database)s.recommendation_user.external_id="%(user)s"
        #        AND %(database)s.recommendation_inventory.user_id=%(database)s.recommendation_user.id
        #        AND %(database)s.recommendation_inventory.item_id=%(database)s.recommendation_item.id;
        #    """ % {
        #    "database": settings.DATABASES["default"]["NAME"],
        #    "user": user_external_id,
        #    "item": item_external_id}
        #cursor = connection.cursor()
        #a = cursor.execute(query)
        #if a == 0:
        #    raise OperationalError("Item not deleted")
        i = Inventory.objects.get(item=Item.item_by_external_id[item_external_id],
                                  user=User.user_by_external_id[user_external_id])
        i.dropped_date = now()
        i.save()

    def get(self, request, user_external_id):
        """
        Get the users owned items. It receives an extra set of GET parameters. The offset and the items.

        The ´´offset´´ represents the amount of items to pass before start sending results.
        The ´´items´´ represents the amount of items to show.

        :param request: The HTTP request.
        :param user_external_id: The user external id that are making the request.
        :type user_external_id: str
        :return: A list of app external ids of the user owned (items that are in database with reference to this
         user and the dropped date set to null).
        """
        offset = int(request.GET.get("offset", 0))  # Offset of items
        number_of_items = int(request.GET.get("items", 20))  # Number of items to present
        limit = offset+number_of_items
        try:
            items = Inventory.objects.filter(user__external_id=user_external_id)
            items = items.order_by("acquisition_date")
            items = items.values_list("item__external_id", "acquisition_date", "dropped_date")[offset:limit]
            items = [{"external_id": int(item), "acquisition_date": date, "dropped_date": removed_date}
                     for item, date, removed_date in items]
        except User.DoesNotExist:
            return self.format_response(self.NOT_FOUND_ERROR_MESSAGE, status=NOT_FOUND_ERROR)
        data = {"user": user_external_id, "items": items}
        return self.format_response(data)

    def post(self, request, user_external_id):
        """
        Puts a new item in the user owned items. It should have a special POST parameter (besides the csrf token or
        other token needed to the connection - to development and presentation purposes the csrf was disabled) that is
        item_to_acquire.

        The ´´item_to_acquire´´ is the item external id that is supposed to be in the user inventory.

        :param request: The HTTP request.
        :param user_external_id: The user external id that are making the request.
        :type user_external_id: str
        :return: A success response if the input was successful =p
        """
        try:
            item_id = request.DATA["item_to_acquire"]
        except KeyError:
            return self.format_response(PARAMETERS_IN_MISS, status=FORMAT_ERROR)

        self.insert_acquisition(user_external_id, item_id)
        #User.user_by_external_id[user_external_id].owned_items = Item.item_by_external_id[item_id]
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
