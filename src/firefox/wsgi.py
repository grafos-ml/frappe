"""
WSGI config for firefox project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "firefox.settings")

from django.core.wsgi import get_wsgi_application
from recommendation.models import TensorModel, PopularityModel

application = get_wsgi_application()
PopularityModel.load_to_cache()
TensorModel.load_to_cache()
