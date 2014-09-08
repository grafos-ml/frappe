#-*- coding: utf-8 -*-
"""
Created on September 1, 2014

Log based re-ranker. I reads the logs from this user and re-rank items from the original recommendation order.

"""
__author__ = "joaonrb"

from recommendation.simple_logging.models import LogEntry


class SimpleLogFilter(object):
    """
    .. py:attribute:: gravity_point - A function or callable object to calculate the gravity point given the \
        request array.

    This first implementation of the re-ranker is intend to produce a withdraw or boost in each item "pre-recommended"
    based in the app position, the app position in previous recommendations and clicks by the user. For this task
    we are assuming that:

    - Is more fair to an item to fall if it experiments an higher improvement that an app that is lower than its normal.
    - The more clicks an item have, the more powerful will be the boost (positive or negative).
    - Is fair for the re-ranker to make not so disturbing moves on each app ranking in order to re-arrange them. This \
    way the changes will be smother.

    """
    points = (
        lambda x: (x.value-5)/2.,  # LogEntry.RECOMMEND
        lambda x: 0,  # LogEntry.CLICK_RECOMMENDED
        lambda x: 5,  # LogEntry.INSTALL
        lambda x: 10,  # LogEntry.REMOVE
        lambda x: -3,  # LogEntry.CLICK
    )

    @staticmethod
    def evaluate(log):
        return SimpleLogFilter.points[log.type](log)

    def __call__(self, user, recommendation, size=4, **kwargs):
        """
        Calculate the new rank based on logs
        """
        logs = LogEntry.logs_for.get(user.pk, [])
        #m = recommendation.mean()
        #print m
        #rec = {v: k for k, v in enumerate(recommendation, start=1)}
        for log in logs:
            recommendation[log.item_id-1] += (self.evaluate(log) * 0.01)
        return recommendation


