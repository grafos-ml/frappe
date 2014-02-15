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
from django.db.models import Count, Sum
import numpy as np

MAX_LOG = 120000


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

    def __init__(self, constant=2, gravity_point=np.mean):
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

    def __call_prototype__(self, user, app_score):
        """
        I will do this documentation latter
        """
        # Get the last "MAX_LOG"s logs ordered by timestamp
        logs = RLog.objects.filter(item__id__in=app_score, user=user).order_by("-timestamp").values_list(
            "item__pk", "type", "value", "timestamp")[:MAX_LOG]

        # Since there Django is not kind enough to map the entries, I guess I do it myself. I some one knows a way that
        # I'm not aware of, just change it and ask for merge.
        mapped_logs = {}
        for item, log_type, value, timestamp in logs:
            try:
                recommended_sum, log_list = mapped_logs[item]

            except KeyError:
                recommended_sum, log_list = 0, []
            mapped_logs[item] = \
                recommended_sum + 1 if log_type == RLog.RECOMMEND else recommended_sum, \
                log_list + [(item, log_type, value, timestamp)]

        # Calculate the gravity point for each item
        tmp_mapped_logs = {}
        for item, (recommended_sum, log_list) in mapped_logs.iteritems():
            # Get the recommended logs for this item in a generator
            values = (value for _, log_type, value, _ in log_list if log_type == RLog.RECOMMEND)

            # Calculate the gravity point
            try:
                gravity_point = self._gravity_point(values)
            except AttributeError or ZeroDivisionError:
                gravity_point = \
                    sum((value for _, log_type, value, _ in log_list if log_type == RLog.RECOMMEND)) / len(log_list)

            # Add it to the mapped items
            tmp_mapped_logs[item] = gravity_point, recommended_sum, log_list
        mapped_logs = tmp_mapped_logs

        # Now we ready. Lets re-rank them

        # First get all the variables by their app rank (GENERATOR)
        ranked_variables = enumerate(((e, mapped_logs[e] if e in mapped_logs.keys() else (i, 0, []))
                                      for i, e in enumerate(app_score, start=1)), start=1)

        # Than we calculate the new rank for each app based on new scores (new rank, item)
        new_scores = (((len(app_score)/gravity_point)**recommended_sum, item)
                      for rank, (item, (gravity_point, recommended_sum, log_list)) in ranked_variables)

        # Now we just nee to sort them by the new rank and send an "item_id only" list
        result = [item_id for _, item_id in sorted(new_scores, cmp=lambda x, y: cmp(x[0], y[0]))]

        # Just a quick check in the result, see if it makes sense
        assert result != app_score or len(RLog.objects.filter(item__id__in=app_score, user=user, type=0)) == 0, \
            "This isn't doing anything"
        assert len(result) == len(app_score), \
            "Some one was messing with the result len (original:%s, result:%s" % (len(app_score), len(result))
        return result

    def __call__(self, user, early_recommendation):
        """
        The real, optimized, not redundant at all call method for the simple log based re-ranker or whatever. With this
        algorithm we will need no more plains to get around in the sky. Just call this method and it will re-rank the
        sh%t out of the recommender.

        :param user: The user that want to know what he wants for apps.
        :type user: ffos.models.FFOSUser
        :param early_recommendation A list with recommendation ids in order to be recommended (ranked).
        :type early_recommendation: list.
        :return: A new set of recommendations ready to fill every app need for the user.
        :rtype: A list of app ids(int).
        """
        # Lets start by making a proper query that receive a list of tuples with:
        # (item id, type of log, sum(values), count, count_type)... This should be enough to a good re-ranker
        logs = RLog.objects.filter(item__id__in=early_recommendation, user=user, type=RLog.RECOMMEND)
        logs = logs.values("item__pk")
        logs = logs.annotate(count=Count("item__pk"), sum=Sum("value"))

        # Just make a quick mapping for the items
        mapped_items = {}
        for log_info in logs:
            item_pk, count, sum_value = log_info["item__pk"], log_info["count"], log_info["sum"]
            mapped_items[item_pk] = count, float(sum_value)

        # Now get the variables ranks
        ranked_variables = enumerate(((app_id, mapped_items.get(app_id) or (0, 0))
                                      for app_id in early_recommendation), start=1)

        # And Get the new scores
        #new_scores = (((len(early_recommendation)/(sum_value/count))**count, item)
        #              for rank, (item, (count, sum_value)) in ranked_variables)
        new_scores = []
        number_of_apps = len(early_recommendation)
        for rank, (item, (count, sum_value)) in ranked_variables:
            try:
                mean = sum_value/count
                #new_rank = (number_of_apps / mean) ** count
                new_rank = rank - mean ** count
            except ZeroDivisionError:
                new_rank = rank
            #print new_rank
            new_scores.append((new_rank, item))

        # We just need to sort
        result = [item_id for _, item_id in sorted(new_scores, cmp=lambda x, y: cmp(x[0], y[0]))]

        #assert result == self.__call_prototype__(user, early_recommendation), \
        #    "Call and call_prototype are not producing the same result"
        return result