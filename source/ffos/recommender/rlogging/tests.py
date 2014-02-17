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
from ffos.models import FFOSUser
from ffos.recommender.rlogging.rerankers import SimpleLogReRanker


class TestSimpleLogReRanker(object):
    """

    """

    def setup(self):
        """
        Start the controller. Get an "virgin" recommendation(without filters or re ranker) and get a set of
        recommendations producing logs.
        """
        self.controller = SimpleController()
        self.user = FFOSUser.objects.order_by("?")[0]
        self.original_recommendation = self.get_app_significance_list(user=self.user,
                                                                       u_matrix=self.controller.get_user_matrix(),
                                                                       a_matrix=self.controller.get_apps_matrix())
        self.controller.registerReranker(SimpleLogReRanker())
        self.log_recommendations = [self.controller.get_recommendation(user=self.user, n=None) for _ in xrange(50)]

    def test_installed_apps_are_off(self):
        """
        Check if installed apps are pushed behind
        """
        installed_app = list(self.user.installed_apps.all())
        for recommendation in self.log_recommendations:
            assert all((app.pk in recommendation[0-len(installed_app):] for app in installed_app)), \
                "Installed apps are note being pushed back"

    def test_difference_between_recommendations(self):
        pass