# -*- coding: utf-8 -*-
"""
.. module:: ffos.recommender.rlogging.tests
    :platform: Unix, Windows
    :synopsis: Test the Logging system and re-ranker based on logs
     Created Fev 17, 2014

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from ffos.recommender.controller import SimpleController
from ffos.models import FFOSUser, FFOSApp
from ffos.recommender.rlogging.rerankers import SimpleLogReRanker
import numpy as np


class TestSimpleLogReRanker(object):
    """

    """
    controller = None
    user = None
    original_recommendation = None
    log_recommendations = None

    @classmethod
    def setup_class(cls):
        """
        Start the controller. Get an "virgin" recommendation(without filters or re ranker) and get a set of
        recommendations producing logs.
        """
        cls.controller = SimpleController()
        cls.user = FFOSUser.objects.order_by("?")[0]
        cls.original_recommendation = cls.controller.get_app_significance_list(
            user=cls.user, u_matrix=cls.controller.get_user_matrix(), a_matrix=cls.controller.get_apps_matrix())
        cls.original_external_ids = cls.controller.get_external_id_recommendations(user=cls.user, n=None)
        cls.original_recommendation = \
            [aid+1 for aid, _ in sorted(enumerate(cls.original_recommendation.tolist()),
                                        cmp=lambda x, y: cmp(y[1], x[1]))]
        cls.controller.registerReranker(SimpleLogReRanker())
        cls.log_recommendations = [cls.controller.get_recommendation(user=cls.user, n=None) for _ in xrange(50)]

    def test_installed_apps_are_off(self):
        """
        [SimpleLogReRanker] Check if installed apps are pushed behind
        """
        installed_app = list(self.user.installed_apps.all())
        for recommendation in self.log_recommendations:
            assert all((app.pk in recommendation[0-len(installed_app):] for app in installed_app)), \
                "Installed apps are note being pushed back"

    def test_recommendation_has_same_number(self):
        """
        [SimpleLogReRanker] Check if the recommendation has the same number has original recommendations
        """
        for recommendation in self.log_recommendations:
            assert len(recommendation) == len(self.original_recommendation), \
                "Some new recommendation don't have the same number as the original."

    def test_recommendation_has_same_items(self):
        """
        [SimpleLogReRanker] Check if recommendations has the same apps that exist in the original.
        """
        for recommendation in self.log_recommendations:
            assert all((app_id in self.original_recommendation for app_id in recommendation)), \
                "Some item exists in some new recommendation but not in the original."

    def test_difference_between_recommendations(self):
        """
        [SimpleLogReRanker] Check if there are variance in the results
        """
        data = {}
        for recommendation in [self.original_recommendation] + self.log_recommendations:
            for index, app_id in enumerate(recommendation, start=1):
                try:
                    data[app_id].append(index)
                except KeyError:
                    data[app_id] = [index]

        data_mean_var = ((app_id, np.mean(indexes), np.std(indexes)) for app_id, indexes in data.iteritems())
        for app_id, mean, sd in data_mean_var:
            assert sd != 0, "The app %d don't move from %d" % (app_id, mean)

    def test_get_recommendations_external_ids(self):
        """
        [SimpleLogReRanker] Check if recommendation by external id sends the correct recommendation
        """
        assert len(self.original_recommendation) == len(self.original_external_ids), \
            "Number of recommendations are different"
        apps = {app.pk: app for app in FFOSApp.objects.filter(id__in=self.original_recommendation)}
        for i in xrange(len(self.original_recommendation)):
            assert apps[self.original_recommendation[i]].external_id == self.original_external_ids[i], \
                "Some external ids don't correspond to the original ids."