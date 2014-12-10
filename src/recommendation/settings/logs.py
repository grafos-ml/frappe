# -*- coding: utf-8 -*-
"""
frappe - recommendation.settings
joaonrb, 26 November 2014

Logging recommendation.settings.
"""

from __future__ import division, absolute_import, print_function
from os import getenv
import logging.handlers

__author__ = "joaonrb"

HOSTNAME = getenv('HOSTNAME')
SYSLOG_TAG = "http_app_frappe"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "root": {
        "level": "WARNING",
        "handlers": ["sentry"],
    },
    'formatters': {
        'simple': {
            "format": "{0} {1}: %(name)s:%(levelname)s %(message)s "
            ":%(pathname)s:%(lineno)s".format(HOSTNAME, SYSLOG_TAG)
        },
    },
    "handlers": {
        "console": {
            "()": logging.StreamHandler,
            "formatter": "simple",
        },
        "syslog": {
            "class": "mozilla_logger.log.UnicodeHandler",
            "facility": logging.handlers.SysLogHandler.LOG_LOCAL7,
            "formatter": "simple",
        },
        "sentry": {
            "level": "ERROR",
            "class": "raven.contrib.django.raven_compat.handlers.SentryHandler",
            },
        },
    "loggers": {
        "django": {
            "level": "DEBUG",
            "handlers": ["console", "syslog"],
            "propagate": False,
        },
        "django.db.backends": {
            "level": "ERROR",
            "handlers": ["console", "syslog"],
            "propagate": False,
        },
        "raven": {
            "level": "DEBUG",
            "handlers": ["console", "syslog"],
            "propagate": False,
            },
        "sentry.errors": {
            "level": "DEBUG",
            "handlers": ["console", "syslog"],
            "propagate": False,
        },
    },
}
