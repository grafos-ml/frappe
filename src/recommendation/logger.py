__author__ = 'joaonrb'


from django.conf import settings
from recommendation.decorators import NoLogger


if hasattr(settings, "RECOMMENDATION_LOGGER"):
    logger_parts = settings.RECOMMENDATION_LOGGER.split(".")
    mod, cls = ".".join(logger_parts[:-1]), logger_parts[-1]
    log_event = getattr(__import__(mod, fromlist=[""]), cls)
    CLICK = log_event.CLICK
    ACQUIRE = log_event.ACQUIRE
    REMOVE = log_event.REMOVE
    RECOMMEND = log_event.RECOMMEND
else:
    log_event = NoLogger
    CLICK = 0
    ACQUIRE = 0
    REMOVE = 0
    RECOMMEND = 0