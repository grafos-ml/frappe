"""
WSGI config for firefox project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "firefox.settings")

from django.core.wsgi import get_wsgi_application
from django.core.cache import get_cache
from recommendation.models import Item, User
from recommendation.language.models import Locale
from recommendation.model_factory import TensorCoFi, Popularity
from recommendation.diversity.models import Genre
from recommendation.ab_testing.models import Experiment

get_cache("default").clear()
get_cache("models").clear()
application = get_wsgi_application()
Popularity.load_to_cache()
TensorCoFi.load_to_cache()
Item.load_to_cache()
User.load_to_cache()
User.load_owned_items()
Locale.load_unsupported_items_by_locale()
Genre.load_to_cache()
Experiment.load_to_cache()
