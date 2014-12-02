#!/usr/bin/env python
#! -*- coding: utf-8 -*-
"""
Frappe fill - Fill database

Usage:
  module init [--verbose <level>] [--module <path>] <module>
  module delete [--verbose <level>] <module>
  module train [--verbose <level>] <module>
  module reloadslots [--verbose <level>]
  module edit  [--verbose <level>] add (filter | reranker) <identifier> <class> [<args>] [<kwargs>] <module>
  module edit  [--verbose <level>] remove (filter | reranker) <identifier> <module>
  module --help
  module --version

Options:
  -m --module=<path>               Pass a json file with settings for the module.
  -v --verbose=<level>             Set verbose mode from 1 to 3 [default: 2].
  -h --help                        Show this screen.
  --version                        Show version.
"""

__author__ = "joaonrb"

import json
import sys
import traceback
import logging
import numpy as np
from django_docopt_command import DocOptCommand
from frappe.models import Module, Predictor, PredictorWithAggregator, Slot, Item, PythonObject, Filter, ReRanker


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


class FrappeCommand(object):

    def __init__(self, parameters):
        self.parameters = parameters
        self.module = None
        if "<module>" in parameters:
            self.module_identifier = parameters["<module>"]
            try:
                self.module = Module.objects.get(identifier=self.module_identifier)
            except Module.DoesNotExist:
                pass
        if self.parameters["--module"]:
            with open(self.parameters["--module"], "r") as f:
                self.settings = json.load(f)
        else:
            self.settings = DEFAULT_SETTINGS
        if self.parameters["--verbose"] == 2:
            logging.getLogger().setLevel(logging.INFO)
        elif self.parameters["--verbose"] == 3:
            logging.getLogger().setLevel(logging.DEBUG)

    def run(self):
        if self.parameters["init"]:
            self.init()
            self.reset()
            self.module.save()
            self.add_predictors()
            self.add_filter()
            self.add_re_ranker()
        elif self.parameters["delete"]:
            self.module.delete()
        elif self.parameters["train"]:
            self.train()
        elif self.parameters["reloadslots"]:
            self.load_slots()
        elif self.parameters["edit"]:
            if self.parameters["remove"]:
                if self.parameters["filter"]:
                    Filter.objects.filter(module=self.module, identifier=self.parameters["<identifier>"]).delete()
                elif self.parameters["reranker"]:
                    ReRanker.objects.filter(module=self.module, identifier=self.parameters["<identifier>"]).delete()
                else:
                    print __doc__
                    return
            elif self.parameters["add"]:
                if self.module:
                    conf = {
                        "identifier": self.parameters["<identifier>"],
                        "class": self.parameters["<class>"],
                        "args": self.parameters["<args>"] or (),
                        "kwargs": self.parameters["<kwargs>"] or {}
                    }
                    obj = self.__to_python__(conf)
                    if self.parameters["filter"]:
                        logging.debug("Filter %s created" % conf["identifier"])
                        Filter.objects.create(module=self.module, obj=obj)
                        logging.debug("Filter %s added to module %s" % (conf["identifier"], self.module_identifier))
                    elif self.parameters["reranker"]:
                        logging.info("Re-Ranker %s created" % conf["identifier"])
                        ReRanker.objects.create(module=self.module, obj=obj)
                        logging.debug("Re-Ranker %s added to module %s" % (conf["identifier"], self.module_identifier))
                    else:
                        print __doc__
                        return
                elif self.module_identifier:
                    logging.warn("Module %s was not initiated" % self.module_identifier)
                else:
                    logging.warn("Forget the module")
            else:
                print __doc__
                return
        else:
            print __doc__
            return
        logging.info("Done")

    def init(self):
        if self.module:
            logging.warn("Module %s already exist. Nothing to be done here." % self.module_identifier)
            return
        self.module = Module(identifier=self.module_identifier)
        logging.debug("Module %s created" % self.module_identifier)

    def add_predictors(self):
        for p in self.settings["predictors"]:
            predictor = Predictor.objects.create(identifier=p["identifier"], python_class=p["class"],
                                                 kwargs=p.get("kwargs", {}))
            logging.debug("Predictor %s created" % p["identifier"])
            PredictorWithAggregator.objects.create(module=self.module, predictor=predictor, weight=p["power"])
            logging.debug("Predictor %s added to module %s" % (p["identifier"], self.module_identifier))

    @staticmethod
    def __to_python__(json_obj):
        identifier = json_obj["identifier"]
        args, kwargs = json_obj.get("args", ()), json_obj.get("kwargs", {})
        class_parts = json_obj["class"].split(".")
        module, cls = ".".join(class_parts[:-1]), class_parts[-1]
        obj = getattr(__import__(module, fromlist=[""]), cls)(*args, **kwargs)
        return PythonObject.objects.create(identifier=identifier, obj=obj)

    def add_filter(self):
        if self.module:
            for f in self.settings["filters"]:
                obj = self.__to_python__(f)
                logging.debug("Filter %s created" % f["identifier"])
                Filter.objects.create(module=self.module, obj=obj)
                logging.debug("Filter %s added to module %s" % (f["identifier"], self.module_identifier))
        elif self.module_identifier:
            logging.warn("Module %s was not initiated" % self.module_identifier)
        else:
            logging.warn("Forget the module")

    def add_re_ranker(self):
        if self.module:
            for r in self.settings["rerankers"]:
                obj = self.__to_python__(r)
                logging.info("Re-Ranker %s created" % r["identifier"])
                ReRanker.objects.create(module=self.module, obj=obj)
                logging.debug("Re-Ranker %s added to module %s" % (r["identifier"], self.module_identifier))
        elif self.module_identifier:
            logging.warn("Module %s was not initiated" % self.module_identifier)
        else:
            logging.warn("Forget the module")

    def reset(self):
        self.module.listed_items = \
            np.array([ieid for ieid, in Item.objects.all().order_by("pk").values_list("external_id")])
        self.module.items_index = {item: index for index, item in enumerate(self.module.listed_items)}
        logging.debug("Reset module %s items" % self.module_identifier)

    @staticmethod
    def load_slots():
        Slot.update_modules()
        logging.debug("System slots reloaded")

    def __train__(self, module_predictor):
        module, predictor = module_predictor.module, module_predictor.predictor
        logging.debug("Training %s", predictor)
        Module.get_predictor(module.pk, predictor.pk).train()
        logging.debug("Finish training %s" % predictor)

    def train(self):
        predictors = PredictorWithAggregator.objects.filter(module__identifier=self.module).select_related()
        for module_predictor in predictors:
            self.__train__(module_predictor)
