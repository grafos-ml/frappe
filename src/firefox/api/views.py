# -*- coding: utf-8 -*-

"""
Created at Fev 19, 2014

API for the firefox application in the recommendation system

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
from recommender.models import Item, User, Inventory
from recommender.records.models import Record
from recommender.diversity.rerankers import DiversityReRanker
from firefox.models import Details

from recommender.api.views import AbstractGoToItem, RecommendationAPI, NOT_FOUND_ERROR


class GoToItem(AbstractGoToItem):
    """
    .. py:class:: ffos.recommender.api.views.GoToItemStore()

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
        slug = Details.objects.filter(external_id=item_external_id).values_list("slug")[0]
        return HttpResponseRedirect(Details.slug_to_item_place(slug))


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

    ITEM_EXPOSED_ATTRIBUTES = ["name", "details__url", "id"]

    def get(self, request, item_external_id):
        """
        Get item details.

        :param request: The HTTP request
        :param item_external_id: The item external id that the details should be send.
        :type item_external_id: str
        :return: A HTTP response with the item information
        """
        try:
            item = Item.objects.filter(external_id=item_external_id).values(*self.ITEM_EXPOSED_ATTRIBUTES)[0]
        except Item.DoesNotExist:
            return self.format_response(self.NOT_FOUND_ERROR_MESSAGE, status=NOT_FOUND_ERROR)

        rank = request.GET.get("rank", None)
        uri = reverse("go_to_store", kwargs={
            "user_external_id": request.GET.get("user", GoToItem.ANONYMOUS),
            "item_external_id": item_external_id,
            "source": GoToItem.RECOMMENDED if rank else GoToItem.CLICK})
        if rank:
            uri += "?rank=%s" % rank
        response = {"external_id": item_external_id, "name": item["name"], "details": item["details__url"],
                    "store": uri}

        return self.format_response(response)