# -*- coding: utf-8 -*-
"""
A decorator to register events into log. Created on Fev 11, 2014

"""

__author__ = "joaonrb"

from recommendation.simple_logging.models import LogEntry
from recommendation.decorators import ILogger
from recommendation.models import Item
from recommendation.decorators import GoToThreadQueue
import functools


class LogEvent(ILogger):
    """
    Log invents into database
    """

    CLICK = LogEntry.CLICK
    ACQUIRE = LogEntry.INSTALL
    REMOVE = LogEntry.REMOVE
    RECOMMEND = LogEntry.RECOMMEND

    def __init__(self, log_type, *args, **kwargs):
        super(LogEvent, self).__init__(*args, **kwargs)
        self.log_type = log_type
        if self.log_type == self.RECOMMEND:
            self.__call__ = self.log_recommendation

    def log_recommendation(self, function):
        """
        Record a recommendation to the database
        """
        @functools.wraps(function)
        def decorated(user, *args, **kwargs):
            result = function(user, *args, **kwargs)
            r = [LogEntry(user=user, item=Item.item_by_external_id[eid], type=self.log_type) for eid in result]
            GoToThreadQueue(LogEntry.objects.bulk_create)(r)
            return result
        return decorated

    def __call__(self, function):
        @functools.wraps(function)
        def decorated(*args, **kwargs):
            uid, iid = args[0], args[1]
            result = function(*args, **kwargs)
            GoToThreadQueue(LogEntry.objects.create)(user_id=uid, item=Item.item_by_item_external_id[iid],
                                                     type=self.log_type)
            return result
        return decorated