# -*- coding: utf-8 -*-
"""
Provide Cache for FireFox OS recommendation webservice

Created on Dec 5, 2013


.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

"""
from recommendation.models import User
from recommendation.language.models import Locale
import functools
import sys
if sys.version_info >= (3, 0):
    basestring = unicode = str


class CacheUser(object):
    """
    Allow users to be cached
    """

    USER = "USER_%s"

    def __call__(self, function):
        """
        The call of the view.
        """
        @functools.wraps(function)
        def decorated(*args, **kwargs):
            u_id = kwargs["user"]
            if isinstance(u_id, basestring):
                all_users = User.all_users()
                user = all_users[u_id]
                if not user:
                    user = User(external_id=u_id)
                    en = Locale.objects.get(language_code="en")
                    user.save_with(language=en)
                kwargs["user"] = user
            return function(*args, **kwargs)
        return decorated