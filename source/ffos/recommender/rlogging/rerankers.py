#-*- coding: utf-8 -*-
"""
.. module:: ffos.recommender.rlogging.rerankers
    :platform: Unix, Windows
    :synopsis: Log based rerankers. Created on Fev 13, 2014

.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from ffos.recommender.filters import ReRanker
from ffos.recommender.rlogging.models import RLog
from ffos.models import FFOSApp
import numpy as np

MAX_LOG = 120


class SimpleLogReRanker(ReRanker):
    """
    .. py:class:: ffos.recommender.rlogging.rerankers.SimpleLogReRanker([constant=1[, gravity_point=mean]])

        .. py:attribute:: constant - The constant to move the ranking up or down. As little importance to the algorithm.
        .. py:attribute:: gravity_point - A function or callable object to calculate the gravity point given the request
        array.


    About
    -----

    This first implementation of the re-ranker is intend to produce a withdraw or boost in each app "pre-recommended"
    based in the app position, the app position in previous recommendations and clicks by the user. For this task
    we are assuming that:

    - Is more fair to an app fo fall if it experiments an improvement that an app that is lower than its normal.
    - The more clicks an app have, the more powerful will be the boost (positive or negative).
    - Is fair for the re-ranker to make not so disturbing moves on each app ranking in order to re-arrange them. This
    way the changes will be smother.
    """

    def __init__(self, constant=1, gravity_point=np.mean):
        """
        Constructor

        :param constant: Locator for the re-ranker. If set to 0 the re ranker produce the same recommendation as the
         input. Default is 1.
        :type constant: int.
        :type constant: float.
        :param gravity_point: A callable object to calculate the gravity point. It should receive an array of numbers
         and return a gravity point.
        :type gravity_point: collections.Callable.
        """
        self._constant = constant
        self._gravity_point = gravity_point

    def __call__(self, user, app_scores):
        """
        I will do this documentation latter
        """
        logs = RLog.objects.filter(item__id__in=app_scores, user=user).order_by("timestamp").values_list(
            "item", "type", "value", "timestamp")[:MAX_LOG]
        mapped_logs = {}
        for item, log_type, value, timestamp in logs:
            try:
                mapped_logs[item].append((item, log_type, value, timestamp))
            except KeyError:
                mapped_logs[item] = [(item, log_type, value, timestamp)]
