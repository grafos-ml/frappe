__author__ = 'joaonrb'

from django.conf import settings
from recommendation.records.decorators import LogRecommendedApps, LogEventInRecords
from recommendation.ab_testing.models import ABEvent
from recommendation.models import Item
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


class ABEventLogger(LogEventInRecords):
    """
    Log invents into database
    """

    def __call__(self, function):
        @functools.wraps(function)
        def decorated(*args, **kwargs):
            user_external_id, item_external_id = args[0], args[1]
            result = function(*args, **kwargs)
            item = Item.objects.get(external_id=item_external_id)
            r0 = ABEvent.objects.filter(user_id=user_external_id, item=item).order_by("-pk")[0]
            r = ABEvent(user_id=user_external_id, item=item, type=self.log_type, model=r0.model,
                        model_identifier=r0.model_identifier)
            r.save()
            return result
        return decorated