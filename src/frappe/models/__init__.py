__author__ = "joaonrb"


from django.contrib import admin
from frappe.models.base import Item, User, Inventory
from frappe.models.module import AlgorithmData, Module, PythonObject, Predictor, PredictorWithAggregator
from frappe.models.predictors import UserFactors

admin.site.register([Item, User, Inventory])
admin.site.register([AlgorithmData, Module, PythonObject, Predictor, PredictorWithAggregator])