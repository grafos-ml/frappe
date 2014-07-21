__author__ = 'joaonrb'

from django.conf import settings
from recommendation.records.decorators import LogRecommendedApps
from recommendation.ab_testing.models import ABEvent
import functools


class ABLogger(LogRecommendedApps):
    """
    Decorator for AB_testing for recommendation models
    """

    def __init__(self):
        super(ABLogger, self).__init__()
        self.is_this_installed = self.is_this_installed and "recommendation.ab_testing" in settings.INSTALLED_APPS
        self.logger = ABEvent

    def __call__(self, function):
        """
        The call of the view.
        """
        @functools.wraps(function)
        def decorated(*args, **kwargs):
            pos, model, result = function(*args, **kwargs)
            if self.is_this_installed:
                try:
                    user = kwargs["user"]
                except KeyError:
                    user = args[0]
                self.logger.recommended(user, pos, model, *result)
            return result
        return decorated