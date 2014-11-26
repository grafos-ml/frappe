# -*- coding: utf-8 -*-
"""
frappe - recommendation.settings
joaonrb, 26 November 2014

Logging recommendation.settings.
"""

from __future__ import division, absolute_import, print_function
import logging

__author__ = "joaonrb"

SYSLOG_TAG = "http_app_frappe"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "root": {
        "level": "WARNING",
        "handlers": ["sentry"],
    },
    "formatters": {
        "simple": {
            "format": "%(asctime)s %(name)s:%(levelname)s %(hostname)s {0}: "
                      "%(message)s :%(pathname)s:%(lineno)s".format(SYSLOG_TAG)
        },
    },
    "handlers": {
        "syslog": {
            "facility": logging.handlers.SysLogHandler.LOG_LOCAL7,
            "formatter": "simple",
         },
        "sentry": {
            "level": "ERROR",
            "class": "raven.contrib.django.raven_compat.handlers.SentryHandler",
            },
        },
    "loggers": {
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