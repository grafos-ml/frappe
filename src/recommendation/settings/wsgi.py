"""
WSGI config for recommendation project.

Ths is an example of use. the recommendation loads most of trivial info to cache and work with cache directly for
performance improvement.
"""

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from threading import Thread
from django.conf import settings
from recommendation.models import Item, User, TensorCoFi, Popularity


def load_rest():
    User.load_to_cache()

    # Load main models
    Popularity.load_to_cache()
    TensorCoFi.load_to_cache()
    if "recommendation.language" in settings.INSTALLED_APPS:
        from recommendation.language.models import Region
        Region.load_to_cache()
    if "recommendation.diversity" in settings.INSTALLED_APPS:
        from recommendation.diversity.models import ItemGenre, Genre
        Genre.load_to_cache()
        ItemGenre.load_to_cache()


# Load user and items
Item.load_to_cache()
Thread(target=load_rest).start()