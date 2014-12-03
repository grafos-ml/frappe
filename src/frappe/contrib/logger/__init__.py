#! -*- coding: utf-8 -*-
"""
Created on September 1, 2014

Log based re-ranker. I reads the logs from this user and re-rank items from the original recommendation order.

"""

from __future__ import division, absolute_import, print_function
import numpy as np
from scipy import sparse
from frappe.contrib.logger.models import LogEntry

__author__ = "joaonrb"


class DummyLogReRanker(object):
    """
    This first implementation of the re-ranker is intend to produce a withdraw or boost in each item "pre-recommended"
    based in the app position, the app position in previous recommendations and clicks by the user. For this task
    we are assuming that:

    - Is more fair to an item to fall if it experiments an higher improvement that an app that is lower than its normal.
    - The more clicks an item have, the more powerful will be the boost (positive or negative).
    - Is fair for the re-ranker to make not so disturbing moves on each app ranking in order to re-arrange them. This \
    way the changes will be smother.

    """

    def __call__(self, module, user, recommendation, size=4, **kwargs):
        """
        Calculate the new rank based on logs
        """
        logs = LogEntry.get_logs_for(module.pk, user.external_id)
        if len(logs):
            indices, data = zip(*logs.items())
            log_matrix = sparse.csr_matrix((data, indices, [0, 2]), shape=(1, len(recommendation)), dtype=np.int8)
            recommendation = np.sum((recommendation, log_matrix)).__array__()
            recommendation.shape = (recommendation.shape[1],)
            return recommendation
        return recommendation