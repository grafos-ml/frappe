"""
WSGI config for mozzila project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frappe_settings.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from django.conf import settings
from recommendation.models import Item, User, TensorCoFi, Popularity


def load_rest():
    if "recommendation.language" in settings.INSTALLED_APPS:
        from recommendation.language.models import Locale, Region
        #Locale.load_to_cache()
        Region.load_to_cache()
    if "recommendation.diversity" in settings.INSTALLED_APPS:
        from recommendation.diversity.models import ItemGenre, Genre
        Genre.load_to_cache()
        ItemGenre.load_to_cache()

# Load user and items
Item.load_to_cache()
# Load main models
#Popularity.load_to_cache()
#TensorCoFi.load_to_cache()
#load_rest()




