.. _installation_and_configuration:

============
Installation
============

Dependencies
------------

For now Frappe is dependent of a few tools in order to work properly.
First, the production server is likely to run with multiple python processes. To increase performance cache is used.
This cache need to be accessible to all processes, so local cache is no good. We currently using ``Memcached``. You can use
other as long it has the standard django cache interface.

Other thing is the lock to cache.For this we use the locks available in uwsgi. Because of this, the use of ``uwsgi`` is
a requisite.

Getting Started
---------------

First thing, you will need to install the python module test.fm independently of the rest:

.. code-block:: bash
   :linenos:

       $ pip install https://github.com/grafos-ml/test.fm/archive/v1.0.4.tar.gz

Then run the setup on the package agfter donload it from Github_:

.. code-block:: bash
   :linenos:

       $ ./setup.py install

Or using pip from the link:

.. code-block:: bash
   :linenos:

       $ pip install https://github.com/grafos-ml/frappe/archive/v2.0.dev.zip

Configuration
_____________

For a moment we have a very manual installation process. This will be replaced with pip style installs any time soon.

1. First you need to add recommendation module to the installed apps in Django settings of the main project:

.. code-block:: python
   :linenos:

       # settings.py

       INSTALLED_APPS = (
            ...  # A ton of cool Django apps
            # Apps need for the recommendation
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.staticfiles",
            # Recommendation apps
            "recommendation",
            "recommendation.api",
            "recommendation.filter_owned",
            "recommendation.language",
            "recommendation.simple_logging",
       )

       # Middleware needed
       MIDDLEWARE_CLASSES = [
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.middleware.transaction.TransactionMiddleware",
            "django.middleware.cache.UpdateCacheMiddleware",
            "django.middleware.cache.FetchFromCacheMiddleware",
       ]

       # Need to have a default cache and a robust cache engine.
       CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
                "LOCATION": "127.0.0.1:11211",
            }
        }

    You will also to change the wsgi.py file to import the application variable from recommendation wsgi.py:

.. code-block:: python
   :linenos:

       # wsgi.py

       import os
       os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_django_app.settings")

       from recommendation.wsgi import application

    And last file the urls.py on your project to:

.. code-block:: python
   :linenos:

       from django.conf.urls import patterns, include, url

       urlpatterns = patterns('', url(r'^', include("recommendation.urls")))

    2. Next, you need to create the Django modules using.

.. code-block:: bash
   :linenos:

       $ ./manage.py syncdb

    3. Now you have to fill the database with applications and user data. For the example we use a dummy data
    from the data folder. You should replace the path to the real path of the marketplace dumps. For now,
    lets start with the dummy data.

.. code-block:: bash
   :linenos:

       $ ./manage.py fill items recommender/package/path/src/bin/data/app/
       $ ./manage.py fill users recommender/package/path/src/bin/data/user

    4. To retrieve recommendations a recommendation model (statistical representation of your data) must be built.
    To have it built you have to run the script:

.. code-block:: bash
   :linenos:

       $ ./manage.py modelcrafter train tensorcofi  # For tensorcofi model
       $ ./manage.py modelcrafter train popularity  # For Popularity

.. note::

    This models are static and represent popularity recommendation and tensorCoFi (TF) factor matrix for the user and
    item population at the moment they are build. Because of that, it doesn't make sense to build any model with no
    users or items in the database. Also, you will want to rebuild the models once in a while, as the users and items
    will be added and new connections between user and item are created.

In reality, you will need some data about users and items in your system. The popularity model is used when the system has few
information about a user. And the TF in case that the system has some (>3 apps installed) info about the user.

This script is shipping with the recommendation framework and builds this matrix. You will want to continue to build
the matrix for new users and items to be included. Keep that in mind.

And voilá, you got your self a recommendation system for your precious little web site. It's a bit static though.

.. code-block:: bash
   :linenos:

       $ ./manage.py runserver

    Open firefox browser at http://127.0.0.1:8000/


5. Now you can try to access also the REST API. The full documentation of APIs can be found through the Table of Content.
For example, to generate JSON response just point your web browser to this
`link <http://localhost:8000/api/v2/recommend/5/002c50b7dae6a30ded5372ae1033da43bba90b4d477733375994791e758fbee0.json>`_.

.. note:: This is the example settings for the firefox dummy data that the developer is working with. The module firefox
 is a working example with a mysql DB that I am working locally. If you change the db settings in firefox module you can
 use the script manager_firefox.py that is installed with setup and avoid major deployment.

Plugin Installations
____________________

To remove the "statiness" of the recommendations you can always install new plugins. The recommendation framework ships
with some pretty neat plugins. Installed in the same way any Django app is installed. Just keep in mind one thing. In
case of re-rankers and filters, your system should do some actions before others. For instance, you may want
that your recommendation have always a big diversity in genre but that don't send every time the same items. Because of
that you also have to use a special settings environment called RECOMMENDATION_SETTINGS. This variable is a dictionary,
much like a static configuration. You also have a default standard and might have more to use in special situations. Basically, it
a core engine(the structure that request the recommendation and use the filters and re-rankers), A list of filters and
another list for re-rankers. Typically, the filters will execute first and re-rankers after and the execute in the same
order that they are registered in RECOMMENDATION_SETTINGS. It will also need a logger class. The logger class is a
decorator that will record the events in some way.

.. code-block:: python
   :linenos:

       # settings.py

       INSTALLED_APPS = (
            ...  # A ton of cool Django apps
            "recommendation",
            "recommendation.diversity",  # First do diversity
            "recommendation.records",  # Than re-rank based on records
            ...
       )

       RECOMMENDATION_SETTINGS = {
        "default": {
            "core": "recommendation.core.TensorCoFiController",
            "filters": [
                "recommendation.filter_owned.filters.FilterOwned",
                "recommendation.language.filters.SimpleLocaleFilter",
                "recommendation.simple_logging.filters.SimpleLogFilter",
                ],
            "rerankers": [
                #"recommendation.diversity.rerankers.simple.SimpleDiversityReRanker"
            ]
        },
        "logger": "recommendation.simple_logging.decorators.LogEvent"
    }

    Now you have an awesome recommendation system.

.. _Django: https://www.djangoproject.com/
.. _Github: https://github.com/grafos-ml/frappe
.. _Issue Tracker: https://github.com/grafos-ml/frappe/issues
.. _test.fm: https://github.com/grafos-ml/test.fm