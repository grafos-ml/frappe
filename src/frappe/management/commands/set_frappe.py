#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Frappe fill - Fill database

Usage:
  set_frappe init
  set_frappe --help
  set_frappe --version

Options:
  -v --verbose                     Set verbose mode.
  -h --help                        Show this screen.
  --version                        Show version.
"""

__author__ = "joaonrb"

import sys
import traceback
from django_docopt_command import DocOptCommand
from django.conf import settings
from frappe.models import Module, Predictor, PredictorWithAggregator, Slot, Item


class Command(DocOptCommand):
    docs = __doc__

    def handle_docopt(self, arguments):
        # arguments contains a dictionary with the options
        try:
            frappe_command = FrappeCommand(arguments)
            frappe_command.run()
        except:
            traceback.print_exception(*sys.exc_info())


DEFAULT_SETTINGS = {
    "default": {
        "predictors": [
            {
                "identifier": "TensorCoFi()",
                "class": "frappe.predictors.TensorCoFiPredictor",
                "power": 0.9
            }, {
                "identifier": "Popularity()",
                "class": "frappe.predictors.PopularityPredictor",
                "power": 0.1
            }
        ],
        "filters": [],
        "rerankers": []
    }
}

FRAPPE_SETTINGS = getattr(settings, "FRAPPE_SETTINGS", DEFAULT_SETTINGS)


class FrappeCommand(object):

    def __init__(self, parameters):
        self.parameters = parameters

    def run(self):
        if self.parameters["init"]:
            self.init()

    def init(self):
        predictors = []
        for name, setts in FRAPPE_SETTINGS.items():
            items = [item_eid for item_eid, in Item.objects.all().order_by("pk").values_list("external_id")]
            module = Module.objects.create(identifier=name, listed_items=items)
            for p in setts["predictors"]:
                predictor = Predictor.objects.create(identifier=p["identifier"], python_class=p["class"],
                                                     kwargs=p.get("kwargs", {}))
                PredictorWithAggregator.objects.create(module=module, predictor=predictor, weight=p["power"])
                predictors.append((module, predictor))

            # Here filters and rerankers
        Slot.update_modules()

        for module, predictor in predictors:
            print "Training", predictor
            Module.get_predictor(module.pk, predictor.pk).train()
