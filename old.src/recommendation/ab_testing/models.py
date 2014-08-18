# -*- coding: utf-8 -*-
"""
Created on 18 July 2014

Models for ab testing

.. moduleauthor:: joaonrb <joaonrb@gmail.com>
"""

import sys
import json
from django.utils.translation import ugettext as _
from django.core.cache import get_cache
from django.contrib import admin
from django.db import models
from django.db.models.signals import post_syncdb
from django.dispatch import receiver
from recommendation.models import User
from recommendation.records.models import Record
from recommendation.decorators import PutInThreadQueue


class Experiment(models.Model):
    """
    AB test version
    """
    name = models.CharField(_("name"), max_length=255, unique=True)
    version = models.PositiveIntegerField(_("version"), max_length=7, default=100000)
    settings = models.TextField(_("settings"))
    is_active = models.BooleanField(_("is active?"), default=False)

    class Meta:
        verbose_name = _("experiment")
        verbose_name_plural = _("experiments")

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    @staticmethod
    def cached_version():
        cache = get_cache("models")
        return cache.get("ab_experiment")

    def put_in_cache(self):
        cache = get_cache("models")
        cache.set("ab_experiment", self, None)

    def save(self, *args, **kwargs):
        if self.is_active:
            try:
                temp = Experiment.objects.get(is_active=True)
                if self != temp:
                    temp.is_active = False
                    temp.save()
            except Experiment.DoesNotExist:
                pass
        super(Experiment, self).save(*args, **kwargs)

    @staticmethod
    def load_to_cache():
        this = Experiment.objects.get(is_active=True)
        this.put_in_cache()
        this.load_to_ab()

    def load_to_ab(self):
        """
        Load This Experiment to AB recommender
        """
        from recommendation.core import get_class, DEFAULT_RECOMMENDATION
        from recommendation.ab_testing.rec_controller import ABTesting
        if not isinstance(DEFAULT_RECOMMENDATION, ABTesting):
            raise EnvironmentError("The default recommendation controller must be ABTesting")
        if self.is_active:
            sets = json.loads(self.settings)["picker"]
            args = []
            kwargs = {}
            for arg in sets.get("args", ()):
                try:
                    c, _, _ = get_class(arg)
                    tmp = c.get_model()
                except IOError:
                    tmp = arg
                args.append(tmp)
            for key, arg in sets.get("kwargs", {}).items():
                try:
                    c, _, _ = get_class(arg)
                    tmp = c.get_model()
                except IOError:
                    tmp = arg
                kwargs[key] = tmp
            picker, args, kwargs = get_class((sets["class"], args, kwargs))
            DEFAULT_RECOMMENDATION.picker = picker(*args, **kwargs)
        else:
            raise AttributeError("This experiment is not active")


class Event(Record):
    """
    Model to associate recommendation.record with ab test records
    """
    model = models.CharField(_("model"), max_length=255, null=True, blank=True)
    model_identifier = models.SmallIntegerField("model id", null=True, blank=True)
    experiment = models.ForeignKey(Experiment, verbose_name=_("experiment"))

    class Meta:
        verbose_name = _("event")
        verbose_name_plural = _("events")

    @staticmethod
    @PutInThreadQueue()
    def recommended(user, model_id, model, *recommended):
        """
        Log Recommended Apps

        :param user: User
        :param recommended: List of items ids
        """
        ab_experiment = Experiment.cached_version()
        if ab_experiment:
            if isinstance(user, User):
                user = user.external_id
            for rank, e_id in enumerate(recommended, start=1):
                Event(user_id=user, item_id=e_id, value=rank, model=model.get_name(), model_identifier=model_id,
                      experiment=ab_experiment).save()
        #logs = [ABEvent(user_id=user, item_id=e_id, value=rank) for rank, e_id in enumerate(recommended, start=1)]
        #ABEvent.objects.bulk_create(logs)
        #post_save.send(sender=Record, instance=logs)


@receiver(post_syncdb, sender=sys.modules[__name__])
def create_default(*args, **kwargs):
    Experiment.objects.get_or_create(
        name="default",
        version=100000,
        settings="""
        {
            "picker": {
                "class": "recommendation.ab_testing.rec_controller.UniformPicker",
                "args": [
                    "recommendation.model_factory.TensorCoFi",
                    "recommendation.model_factory.Popularity"
                ]
            }
        }
        """,
        is_active=True)

admin.site.register([Experiment, Event])