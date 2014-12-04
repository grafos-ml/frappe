"""
WSGI config for recommendation project.

Ths is an example of use. the recommendation loads most of trivial info to cache and work with cache directly for
performance improvement.
"""

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# Load main stuff to cache

import logging
from frappe.models import User, Item, Inventory, Module

Item.load_to_cache()
logging.debug("Items loaded to cache")

User.load_to_cache()
logging.debug("Users loaded to cache")

Inventory.load_to_cache()
logging.debug("Users items loaded to cache")

Module.load_to_cache()
logging.debug("Module loaded to cache")