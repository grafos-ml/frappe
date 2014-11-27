"""
WSGI config for recommendation project.

Ths is an example of use. the recommendation loads most of trivial info to cache and work with cache directly for
performance improvement.
"""

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()