__author__ = "joaonrb"


from django.contrib import admin
from frappe.models.base import Item, User, Inventory
from frappe.models.module import AlgorithmData, Module, PythonObject, Predictor, PredictorWithAggregator

admin.site.register([Item, User, Inventory])
admin.site.register([AlgorithmData, Module, PythonObject, Predictor, PredictorWithAggregator])