#! -*- encoding: utf-8 -*-
"""
Module Loggers
"""

from abc import ABCMeta, abstractmethod
from frappe.contrib.logger.models import LogEntry

__author__ = "joaonrb"


class ILogger(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def recommendation(self, module, user, recommendation):
        """
        log some event
        :param module:
        :param user:
        :param recommendation:
        :return:
        """

    @abstractmethod
    def click(self, user, item):
        """
        Log a click in an item
        :param user:
        :param item:
        :return:
        """

    @abstractmethod
    def acquire(self, user, items):
        """
        Log and acquire item
        :param user:
        :param items:
        :return:
        """

    @abstractmethod
    def drop(self, user, items):
        """
        Log dropping an item
        :param user:
        :param items:
        :return:
        """

    @abstractmethod
    def __str__(self):
        """
        Logger name
        """


class NoLogging(ILogger):
    """
    Doesnt log
    """

    @classmethod
    def recommendation(cls, module, user, recommendation):
        pass

    @classmethod
    def click(cls, user, item):
        pass

    @classmethod
    def acquire(cls, user, items):
        pass

    @classmethod
    def drop(cls, user, items):
        pass

    def __str__(self):
        return "No logging"


class DBLogger(ILogger):
    """
    Log to database
    """

    @staticmethod
    def bulk_logging(log_type, module, user, items):
        new_logs = [
            LogEntry(user=user, item_id=eid, type=log_type, source=getattr(module, "identifier", "NOMODULE"), value=i)
            for i, eid in enumerate(items, start=1)
        ]
        LogEntry.objects.bulk_create(new_logs)
        LogEntry.add_logs(module, user, new_logs)

    @classmethod
    def recommendation(cls, module, user, recommendation):
        cls.bulk_logging(LogEntry.RECOMMEND, module, user, recommendation)

    @classmethod
    def click(cls, user, item):
        log = LogEntry.objects.create(user=user, item_id=item, type=LogEntry.CLICK, source="NOMODULE")
        LogEntry.add_logs(user, (log,))

    @classmethod
    def acquire(cls, user, items):
        cls.bulk_logging(LogEntry.ACQUIRE, None, user, items)

    @classmethod
    def drop(cls, user, items):
        cls.bulk_logging(LogEntry.DROP, None, user, items)

    def __str__(self):
        return "database logging"