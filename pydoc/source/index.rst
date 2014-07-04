
Welcome to Recommendation Framework!
====================================

Recommendation Framework is a Django application that provides item recommendations for users. The simplest form of
recommendations now are based on collaborative filtering tensor matrix. The framework also ships with a set of filters
and re-rankers to give more juice to the recommendation. The point of the framework is to flexible enough to adapt to
most of the services. For this purpose is possible to develop and deploy within the framework "recommendation" plugins
to improve the recommendation, to make it more flexible or whatever some brilliant mind want the framework to do.

Download
--------

Check the repository here. What? It doesn't point to any place? Whats the point with that!?

API Documentation
-----------------

.. toctree::
   :maxdepth: 2

   recommendation.tutorial
   recommendation.documentation
   recommendation.plugins

Get Started
-----------

To get started with the Recommendation framework, you first need to set a Django environment. Do all the thing you need
to do in order to start your django project. If you don't now how to do it you're a bit ahead of yourself. Just check
the `Django <http://djangoproject.com>`_ website and see if it's what you're looking for.

Installation
____________

Like all the good python packages you just use "`pip install recommendation-framework`" and you're ready to go.
Unfortunately this project doesn't even got a real name. As far as I'm concerned it will be called frappe or something
coffee and cream related. Why? This project is the younger brother of the `Frappé
<http://frappe.cc/>`_ another recommendation project developed by `Linas Baltrunas
<http://www.linkedin.com/profile/view?id=34647483>`_, the same guy behind this here. So, in this alpha stage of the
project, to get it just ask nicely to `Linas <mailto:linas.baltrunas@gmail.com>`_ or `João <mailto:joaonrb@gmail.com>`_
and we will think about it. If for some reason they think you are worthy, then you just have to add the package to you
environment.

After that just add it to the installed apps in Django settings:

.. code-block:: python
   :linenos:

   # settings.py

   INSTALLED_APPS = (
        ...  # A ton of cool Django apps
        "recommendation",
        ...
   )

Okay, now you can have ways to retrieve recommendations from the system. Link your users to the
recommendation.models.User and the items you want to be subject of recommendation to recommendation.models.Item.
One more thing. To retrieve recommendations a special model must be built. To have it built you have to run the
script:

.. code-block:: bash
   :linenos:

   >>> modelcrafter.py train tensorcofi  # For tensorcofi model
   >>> modelcrafter.py train popularity  # For Popularity

.. note:: This models are static and represent popularity recommendation and tensorCoFi factor matrix for the user and \
    item population in the moment they are build. Because of that, it doesn't make sense to build any model with no \
    users or items on the database. Also, you will want to rebuild the models once in a wild, as the users and items \
    will be added and new connections between user and item are created.

In good true, you will need the both of them in your system. The popularity model is used when the system has few
information on user. And the other in case that the system has more than enough info on the user.

This script is shipping with the recommendation framework and it build this matrix. You will want to continue to build
the matrix for new users and items to be included. Keep that in mind.

And voilá, you got your self a recommendation system for your precious little web site. It's a bit static though.

Plugin Installations
____________________

To remove the "staticness" of the recommendations you can always install new plugins. The recommendation framework ships
with some pretty neat plugins. Installed in the same way any Django app is installed. Just keep in mind one thing. In
case of re-rankers and filters, your system may what some actions to occur before others. For instance, you may want
that your recommendation have always a big diversity in genre but that don't send every time the same items. Because of
that you also have to use a special settings environment called RECOMMENDATION_SETTINGS. This variable is a dictionary,
much like database. You also have a default standard and might have more to use in special situations. Basically, it
a core engine(the structure that request the recommendation and use the filters and re-rankers), A list of filters and
another list for re-rankers. Typically, the filters will execute first and re-rankers after and the execute in the same
order that they are registered in RECOMMENDATION_SETTINGS.

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
            "core": ("recommendation.core", "Recommender"),
            "filters": [
                ("recommendation.filter_owned.filters", "FilterOwnedFilter"),
                ("recommendation.language.filters", "SimpleLocaleFilter"),
            ],
            "rerankers": [
                # The order witch the re-rankers or filters are setted here represent the order that they are called
                #("recommendation.records.rerankers", "SimpleLogReRanker"),
                ("recommendation.diversity.rerankers", "DynamicDiversityReRanker")
            ]
        }
    }

Now you have a awesome recommendation system.

Example
-------

In the package firefox there is a working example.

#. Create the database::

    $ python manage.py syncdb

#. Fill the database with some data. In the bin folder there are some dummy data::

    $ ./bin/fill_firefox.py items ./bin/data/app
    ...
    $ .bin/fill_firefox.py users ./bin/data/user

#. After this build the TensorCoFi and Popularity models::

    $ .bin/modelcrafter.py train popularity
    $ .bin/modelcrafter.py train tensorcofi

#. Now just run the server::

    $ python manage.py runserver

Now if you use the browser go to localhost:8000 you will access a example frontend that does the api calls.

REST API Installation
---------------------

There is no science behind this. Just implement a web service in the same way django-rest-framework does.

.. toctree::
    :maxdepth: 2

    webservice.v2


