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

from django.conf import settings

if "frappe.contrib.region" in settings.INSTALLED_APPS:
    from frappe.contrib.region.models import Region, UserRegion
    Region.load_to_cache()
    UserRegion.load_to_cache()
    logging.debug("Regions loaded to cache")

if "frappe.contrib.diversity" in settings.INSTALLED_APPS:
    from frappe.contrib.diversity.models import Genre, ItemGenre
    Genre.load_to_cache()
    ItemGenre.load_to_cache()
    logging.debug("Genres loaded to cache")

if "frappe.contrib.logger" in settings.INSTALLED_APPS:
    from frappe.contrib.logger.models import LogEntry
    LogEntry.load_to_cache()
    logging.debug("Logs loaded to cache")