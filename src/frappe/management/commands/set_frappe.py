#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Frappe fill - Fill database

Usage:
  set_frappe init <module>
  set_frappe train <module>
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
import logging
import numpy as np
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
            self.init(self.parameters["<module>"])
        if self.parameters["train"]:
            self.train(self.parameters["<module>"])

    def init(self, module="default"):
        if Module.objects.filter(identifier=module).count():
            logging.info("Module %s already exist" % module)
            return
        predictors = []
        for name, setts in FRAPPE_SETTINGS.items():
            items = np.array([item_eid for item_eid, in Item.objects.all().order_by("pk").values_list("external_id")])
            module = Module.objects.create(identifier=name, listed_items=items)
            for p in setts["predictors"]:
                predictor = Predictor.objects.create(identifier=p["identifier"], python_class=p["class"],
                                                     kwargs=p.get("kwargs", {}))
                PredictorWithAggregator.objects.create(module=module, predictor=predictor, weight=p["power"])
                predictors.append((module, predictor))

            # Here filters and rerankers
        Slot.update_modules()

    def __train__(self, module_predictor):
        module, predictor = module_predictor.module, module_predictor.predictor
        logging.info("Training %s", predictor)
        Module.get_predictor(module.pk, predictor.pk).train()
        logging.info("Finish training %s" % predictor)

    def train(self, module):
        predictors = PredictorWithAggregator.objects.filter(module__identifier=module).select_related()
        for module_predictor in predictors:
            self.__train__(module_predictor)
