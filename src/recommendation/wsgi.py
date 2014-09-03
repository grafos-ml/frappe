"""
WSGI config for recommendation project.

Ths is an example of use. the recommendation loads most of trivial info to cache and work with cache directly for
performance improvement.
"""

import os
if "DJANGO_SETTINGS_MODULE" not in os.environ:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recommendation.default_settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from django.conf import settings
from recommendation.models import Item, User, TensorCoFi, Popularity
# Load user and items
print("Loading items to cache...")
Item.load_to_cache()
print("done!")
print("Loading user to cache...")
User.load_to_cache()
print("done!")

print("Loading popularity to cache...")
# Load main models
Popularity.load_to_cache()
print("done!")

print("Loading tensorcofi to cache...")
TensorCoFi.load_to_cache()
print("done!")


if "recommendation.language" in settings.INSTALLED_APPS:
    print("Loading languages to cache...")
    from recommendation.language.models import Locale
    Locale.load_to_cache()
    print("done!")


if "recommendation.simple_logging" in settings.INSTALLED_APPS:
    print("Loading logs to cache...")
    from recommendation.simple_logging.models import LogEntry
    LogEntry.load_to_cache()
    print("done!")

if "recommendation.diversity" in settings.INSTALLED_APPS:
    print("Loading genres to cache...")
    from recommendation.diversity.models import ItemGenre, Genre
    Genre.load_to_cache()
    ItemGenre.load_to_cache()
    print("done!")