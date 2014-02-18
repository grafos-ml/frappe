# -*- coding: utf-8 -*-
"""
.. module:: ffos.api
    :platform: Unix, Windows
    :synopsis: The api module for tastypie implementation.
     Created Fev 17, 2014

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from tastypie.resources import csrf_exempt
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie import fields
from ffos.models import FFOSApp, FFOSUser
import functools


class FFOSResource(ModelResource):

    def determine_format(self, request):
        """
        Used to determine the desired format from the request.format
        attribute.
        """
        if hasattr(request, 'format') and request.format in self._meta.serializer.formats:
            return self._meta.serializer.get_mime_for_format(request.format)
        return super(FFOSResource, self).determine_format(request)

    class WrapView(object):
        """
        This class is used to wrap the views so they may retrieve parameter data from the url. The default just
        retrieve the format.
        """

        def __init__(self, resource, view):
            self._view = super(FFOSResource, resource).wrap_view(view)
            self._wraps = functools.wraps(self._view)
            self._resource = resource

        @csrf_exempt
        def __call__(self, request, *args, **kwargs):
            args, kwargs = self.set_request(request, *args, **kwargs)
            return self._wraps(self._view)(request, *args, **kwargs)

        def set_request(self, request, *args, **kwargs):
            """
            Set some request variables to be used in views
            """
            request.format = kwargs.pop('format', None)
            return args, kwargs


class FFOSUserResource(FFOSResource):
    class Meta:
        queryset = FFOSUser.objects.all()
        resource_name = "users"
        list_allowed_methods = ["get"]
        detail_allowed_methods = ["get"]


class InstalledAppResource(FFOSResource):
    user = fields.ForeignKey(FFOSUserResource, 'user', null=True)

    class Meta:
        queryset = FFOSApp.objects.all()
        resource_name = "user/installed"
        list_allowed_methods = ["get"]
        detail_allowed_methods = ["get", "post"]
        filtering = {
            "users": ALL_WITH_RELATIONS
        }
