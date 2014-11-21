#! -*- encoding: utf-8 -*-
"""
Module Loggers
"""
__author__ = "joaonrb"

from abc import ABCMeta, abstractmethod
from frappe.tools.logger.models import LogEntry


class ILogger(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def recommendation(self, module, user, recommendation):
        """
        log some event
        :param args:
        :param kwargs:
        :return:
        """

    @abstractmethod
    def click(self, module, user, item):
        """
        Log a click in an item
        :param module:
        :param user:
        :param item:
        :return:
        """

    @abstractmethod
    def acquire(self, module, user, items):
        """
        Log and acquire item
        :param module:
        :param user:
        :param items:
        :return:
        """

    @abstractmethod
    def drop(self, module, user, items):
        """
        Log dropping an item
        :param module:
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
    def click(cls, module, user, item):
        pass

    @classmethod
    def acquire(cls, module, user, items):
        pass

    @classmethod
    def drop(cls, module, user, items):
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
            LogEntry(user=user, item_id=eid, type=log_type, source=module.identifier, value=i)
            for i, eid in enumerate(items, start=1)
        ]
        LogEntry.objects.bulk_create(new_logs)
        LogEntry.add_logs(user, new_logs)

    @classmethod
    def recommendation(cls, module, user, recommendation):
        cls.bulk_logging(LogEntry.RECOMMEND, module, user, recommendation)

    @classmethod
    def click(cls, module, user, item):
        log = LogEntry.objects.create(user=user, item_id=item, type=LogEntry.CLICK, source=module.identifier)
        LogEntry.add_logs(user, (log,))

    @classmethod
    def acquire(cls, module, user, items):
        cls.bulk_logging(LogEntry.ACQUIRE, module, user, items)

    @classmethod
    def drop(cls, module, user, items):
        cls.bulk_logging(LogEntry.DROP, module, user, items)

    def __str__(self):
        return "database logging"