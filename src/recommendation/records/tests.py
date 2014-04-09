# -*- coding: utf-8 -*-
"""
Created Fev 17, 2014

Test the Logging system and re-ranker based on logs

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from recommendation.records.rerankers import SimpleLogReRanker
from recommendation.records.decorators import LogRecommendedApps
from recommendation.records.models import Record
from recommendation.models import User


class DummyUser(object):
    class owned_items:
        @staticmethod
        def values(dummy_string):
            return [{"pk": 1}, {"pk": 4}]
    external_id = "dummy_user_for_records"


class TestSimpleLogReRanker(object):
    """
    Testing package for the SimpleLogReRanking re-ranker and the system supporting it.
    """

    @classmethod
    def setup_class(cls):
        """
        Start the controller.
        """
        cls.user = DummyUser()
        cls.re_ranker = SimpleLogReRanker()
        cls.decorator = LogRecommendedApps()

    def test_recording_decorator_without_installed(self):
        """
        [SimpleLogReRanker] Check if the decorator records the recommendation if it is not installed
        """
        dummy_recommendation = [3, 5, 1, 2, 4]
        self.decorator.is_this_installed = False
        self.decorator(lambda: dummy_recommendation)()
        assert Record.objects.all().count() == 0, "Record re-ranker logs the recommendation when is not installed"

    def test_reranker_without_recording(self):
        """
        [SimpleLogReRanker] Check recommendations change without recording
        """
        Record.objects.all().delete()
        assert Record.objects.all().count() == 0, "Records were not deleted"
        dummy_recommendation = [3, 5, 1, 2, 4]
        self.decorator.is_this_installed = False
        self.decorator(lambda user: dummy_recommendation)(self.user.external_id)
        re_ranked_dummy_recommendation = self.re_ranker(self.user, dummy_recommendation[:])
        assert dummy_recommendation == re_ranked_dummy_recommendation, \
            "Re-ranker change the recommendation even without records"

    def test_reranker_with_records(self):
        """
        [SimpleLogReRanker] Check recommendations changes while recording
        """
        Record.objects.all().delete()
        assert Record.objects.all().count() == 0, "Records were not deleted"
        dummy_recommendation = [3, 5, 1, 2, 4]
        self.decorator.is_this_installed = True
        self.decorator(lambda user: dummy_recommendation)(self.user.external_id)
        re_ranked_dummy_recommendation = self.re_ranker(self.user, dummy_recommendation[:])
        print(dummy_recommendation)
        print(re_ranked_dummy_recommendation)
        assert dummy_recommendation != re_ranked_dummy_recommendation, \
            "Re-ranker didn't change the recommendation even without records"