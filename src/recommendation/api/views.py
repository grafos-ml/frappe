# -*- coding: utf-8 -*-

"""
Created at Fev 19, 2014

The views for the Recommend API.
"""
__author__ = "joaonrb"

from django.db.utils import IntegrityError
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from rest_framework.renderers import JSONRenderer, XMLRenderer
from rest_framework.parsers import JSONParser, XMLParser
from rest_framework.views import APIView
from recommendation.models import User, Inventory, Item
from recommendation.core import get_controller
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
    A HttpResponse that renders its content into JSON.
    """
    content_type = "application/json"
    renderer = JSONRenderer()


class XMLResponse(APIResponse):
    """
    A HttpResponse that renders its content into XML.
    """
    content_type = "application/xml"
    renderer = XMLRenderer()


class RecommendationAPI(APIView):
    """
    An "abstract kind" of view class that implements a APIView from rest_framework
    """
    format_parser = None
    format_response = None

    def dispatch(self, request, data_format=JSON, *args, **kwargs):
        """
        Check the format of the request/response by the argument

        :param request: Django HTTP request
        :param data_format: The data format of the request/response. Must be something in "json", "xml",...
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
        :param item_external_id: Item external_id that is clicked.
        :param click_type: The type of click that is.
        :param rank: Rank of the item on recommendation. Default=None.
        :raise OperationalError: When some of the data maybe wrongly inserted into data base
        """


class UserRecommendationAPI(RecommendationAPI):
    """
    A class based view for the recommendation. This View ony support the get method
    """

    http_method_names = [
        "get"
    ]

    def get(self, request, user_external_id, number_of_recommendations=5):
        """
        Get method to request recommendations

        :param request: This is the request. It is not needed but has to be here because of the django interface with
        views.
        :param user_external_id: The user that want the recommendation ore the object of the recommendations.
        :param number_of_recommendations: Number of recommendations that are requested.
        :return: A HTTP response with a list of recommendations.
        """

        # Here is the decorator for recommendation
        recommended_apps = \
            get_controller().get_external_id_recommendations(user_external_id, int(number_of_recommendations))

        data = {"user": user_external_id, "recommendations": recommended_apps}
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
    def insert_acquisition(user, item):
        """
        Insert a new in user installed apps

        :param user: The user.
        :param item: The item.
        :raise OperationalError: When some of the data maybe wrongly inserted into data base
        """
        try:
            inv = Inventory.objects.get(item=item, user=user)
            inv.is_dropped = False
            inv.save()
        except Inventory.DoesNotExist:
            Inventory.objects.create(item=item, user=user)

    @staticmethod
    #@GoToThreadQueue()
    @log_event(log_event.REMOVE)
    def remove_item(user, item):
        """
        Update a certain item to remove in the uninstall datetime field

        :param user: The user id.
        :param item: The item id.
        :raise OperationalError: When some of the data maybe wrongly inserted into data base
        """
        i = Inventory.objects.get(item=item, user=user)
        i.is_dropped = True
        i.save()

    def get(self, request, user_external_id):
        """
        Get the users owned items. It receives an extra set of GET parameters. The offset and the items.

        The ´´offset´´ represents the amount of items to pass before start sending results.
        The ´´items´´ represents the amount of items to show.

        :param request: The HTTP request.
        :param user_external_id: The user external id that are making the request.
        :return: A list of app external ids of the user owned (items that are in database with reference to this
         user and the dropped date set to null).
        """
        offset = int(request.GET.get("offset", 0))  # Offset of items
        number_of_items = int(request.GET.get("items", 0))  # Number of items to present
        limit = (offset+number_of_items) or None
        user = User.get_user_by_external_id(user_external_id)
        try:
            items = [
                {
                    "external_id": Item.get_item_external_id_by_id(item_id),
                    "is_dropped": is_dropped
                } for item_id, is_dropped in User.get_user_items(user.pk).items()[offset:limit]
            ]
        except KeyError:
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
        :return: A success response if the input was successful =p
        """
        try:
            item_id = request.POST["item_to_acquire"]
        except KeyError:
            return self.format_response(PARAMETERS_IN_MISS, status=FORMAT_ERROR)

        self.insert_acquisition(User.get_user_by_external_id(user_external_id), Item.get_item_by_external_id(item_id))
        return self.format_response(SUCCESS_MESSAGE)

    def delete(self, request, user_external_id):
        """
        removes an old item in the user installed apps. It should have a special POST parameter (besides the csrf token
        or other token needed to the connection) that is item_to_acquire.

        The ´´item_to_remove´´ is the item external id that is supposed to be removed in the user inventory.

        :param request: The HTTP request.
        :param user_external_id: The user external id that are making the request.
        :return: A success response if the input was successful =p
        """
        try:
            item_id = request.DATA["item_to_remove"]
        except KeyError:
            return self.format_response(PARAMETERS_IN_MISS, status=FORMAT_ERROR)

        self.remove_item(User.get_user_by_external_id(user_external_id), Item.get_item_by_external_id(item_id))
        return self.format_response(SUCCESS_MESSAGE)