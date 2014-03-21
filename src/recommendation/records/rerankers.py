#-*- coding: utf-8 -*-
"""
Created on Fev 13, 2014

Log based re-ranker. I reads the logs from this user and re-rank items from the original recommendation order.

.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from recommendation.records.models import Record
from django.db.models import Count, Sum, Q

MAX_LOG = 120000
#SIMPLE_RANK_CALCULATOR = lambda rank, mean, count, size: rank + ((size - mean) ** count)
SIMPLE_RANK_CALCULATOR = lambda rank, mean, count, size: mean + ((size - mean) ** count)
"""
Default rank calculator. Makes the item new rank be equal to the *mean* of it position in the recommendation *plus*
the *number of recommendations for request* minus mean elevated to the *number of recommendation that this item has
experienced*.

:param rank: The rank that the item receive in this recommendation
:param mean: The mean of recommendations that this item has so far.
:param count: Number of recommendation that this item has been so far.
:param size: Size of this recommendation set.
"""


class SimpleLogReRanker(object):
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

    def __init__(self, rank_calculator=None):
        """
        Constructor

        :param rank_calculator: A callable object to calculate the new rank. Must receive rank, rank mean, number of \
        recommendations and gravity point. Default is recommendation.record.rerankers.SIMPLE_RANK_CALCULATOR
        :type rank_calculator: collections.Callable
        """
        self._rank_calculator = rank_calculator or SIMPLE_RANK_CALCULATOR

    def __call__(self, user, early_recommendation, size=4, **kwargs):
        """
        The real, optimized, not redundant at all call method for the simple log based re-ranker or whatever. With this
        algorithm we will need no more plains to get around in the sky. Just call this method and it will re-rank the
        sh%t out of the recommendation.

        :param user: The user that want to know what he wants for apps.
        :type user: recommender.models.User
        :param early_recommendation: A list with recommendation ids in order to be recommended (ranked).
        :type early_recommendation: list.
        :return: A new set of recommendations ready to fill every item need for the user.
        :rtype: A list of items ids(int).
        """
        mapped_items = {}
        owned_items = [item["pk"] for item in user.owned_items.values("pk")]
        # Push the installed app to the back. This is needed because this algorithm rearrange rank values
        for item_id in owned_items:
            mapped_items[item_id] = float("inf"), 1  # For already installed apps the stronger push down variables.

        # Lets start by making a proper query that receive a list of tuples with:
        # (item id, type of log, sum(values), count, count_type)... This should be enough to a good re-ranker
        items_in_logs = (item_id for item_id in early_recommendation if item_id not in owned_items)
        logs = Record.objects.filter(item__id__in=items_in_logs, user=user, type=Record.RECOMMEND)
        logs = logs.filter(~Q(value=None)).values("item__pk")
        logs = logs.annotate(count=Count("item__pk"), sum=Sum("value"))

        # Mapping the logged items
        for log_info in logs:
            item_pk, count, sum_value = log_info["item__pk"], log_info["count"], log_info["sum"]
            mapped_items[item_pk] = count, float(sum_value)

        # Now get the variables ranks
        ranked_variables = enumerate(((app_id, mapped_items.get(app_id) or (0, 0))
                                      for app_id in early_recommendation), start=1)

        # And Get the new scores
        new_scores = []

        #number_of_apps = len(early_recommendation)
        for rank, (item, (count, sum_value)) in ranked_variables:
            try:
                mean = sum_value/count
                #new_rank = (number_of_apps / mean) ** count
                new_rank = \
                    self._rank_calculator(rank, mean, count, size if mean+1 < size else (mean+1.5))
            except ZeroDivisionError:
                new_rank = rank
            #print new_rank
            new_scores.append((new_rank, item))

        # We just need to sort
        sorted_items = sorted(new_scores, key=lambda x: x[0])
        assert sorted_items[0][0] < sorted_items[-1][0], "The elements are sorted in the wrong way"

        return [item_id for _, item_id in sorted_items]