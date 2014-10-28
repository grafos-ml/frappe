__author__ = "joaonrb"


from django.contrib import admin
from frappe.models.base import Item, User, Inventory

admin.site.register([Item, User, Inventory])