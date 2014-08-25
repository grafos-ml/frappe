"""
Created at March 11, 2014

The Model Maker
===============

This script turns on the model crafter. The model crafter simple create a model. Than he gos to sleep. When he wakes up
build another model. After lunch another model. And he keeps to craft models until the blue fairy come and turn one of
the models to a real child. That lies a lot. But still the people believe in the recommendations of the child.

How it Works
============

To make the Gepeto to start crafting models just ask really nicely like this::

    $ modelcrafter.py work
    $ modelcrafter.py work until DD-MM-YYYY
    $ modelcrafter.py work until DD-MM every 10 minutes  # Gepeto will assume you talking about this year

To make Gepeto go on vacations just type::

    $ modelcrafter.py stop

To make Gepeto build only one model::

    $ modelcrafter.py train tensorcofi
    $ modelcrafter.py train popularity

Options
=======

Pinocchio does this part. He give me his word.

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

# Configure here the Django settings file location
DJANGO_SETTINGS = "firefox.settings"
CRON_JOB_NAME = "joaonrb"

import sys
import os
from pkg_resources import resource_filename
sys.path.append(resource_filename(__name__, "/../"))

os.environ["DJANGO_SETTINGS_MODULE"] = DJANGO_SETTINGS
from recommendation.models import TensorCoFi, Popularity
from django.core.management.base import BaseCommand, CommandError


class ModelCrafterError(Exception):
    """
    A standard error for this script
    """


class TimeInterval(object):
    """
    The interval of time that Gepeto should deliver a model
    """
    UNITS = {
        "minute": "minute",
        "hour": "hour"
    }

    UNITS_PLURAL = {
        "minutes": "minute",
        "hours": "hour"
    }

    def __init__(self, value, unit):
        self.value = value
        self.unit = (self.UNITS if value == 1 else self.UNITS_PLURAL)[unit]

    def __call__(self, job):
        """
        Set the time in the job

        :param job: The crontab job
        :param value: The value to set
        :param unit: The units of time to set
        """

        getattr(job, self.unit)().every(self.value)
        return job

MODELS = {
    "tensorcofi": TensorCoFi,
    "popularity": Popularity
}


def craft_model(options=[]):
    """
    This crafts a model for the recommendation system.
    """
    MODELS[options].train_from_db()


def work(every, **kwargs):
    """
    Make the job to work
    :param every:
    :return:
    """
    raise NotImplemented
    #cron = crontab.CronTab(user="www", tab="Gepeto")
    #job = cron.new(command="/home/joaonrb/Workspaces/Repository/ffos/src/bin/modelcrafter.py make",
    #               comment="Create one recommendation model and store it in db")
    # every(job)
    #job.minutes.every(2)
    #cron.write()
    #print(cron.render())


OPTIONS = {
    "work": {
        "command": work,
        "args": ["every"],
    },
    "train": {
        "command": craft_model,
        "args": []
    }
}


def main(command, options, every=TimeInterval(1, "minute")):
    """

    :param command:
    :param every:
    :return:
    """
    opt = locals()
    OPTIONS[command]["command"](*(opt[attr] for attr in OPTIONS[command]["args"]), options=options)

#if __name__ == "__main__":
#    command = sys.argv[1]
#    main(command=command)
#    # TODO


class Command(BaseCommand):
    args = "<action option>"
    help = "Trains the model. Currently implemented: train tensorcofi, train popularity."

    def handle(self, *args, **options):
        try:
            main(args[0], args[1])
        except Exception:
            raise CommandError("Wild error appear!!!")