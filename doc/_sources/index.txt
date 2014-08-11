
Welcome to Recommendation Framework!
====================================

Recommendation Framework is a Django application that provides item recommendations for users. The simplest form of
recommendations now are based on collaborative filtering tensor factorisation (TF). We use test.fm framework for
computing the models. The Recommendation Framework then implements a logic to use the models in order to serve recommendations.
The framework ships with a set of filters and re-rankers to implement business rules such as diversity. 
Filters are modules that implement a peace of logic such as "filter out items that users has already installed", whereas, rerankers
implement more complex logic such as enforcing diversity or discounting values for some items.

The framework was originally designed for Firefox OS marketplace but is 
flexible enough to adapt to the most of the application domains. Within the framework it is possible to develop and deploy "recommendation" plugins
that improve the recommendations, make additional business rules, etc.


API Documentation
-----------------

.. toctree::
    :maxdepth: 2

    webservice.v2


How it works
------------
You have a database where you register which user (recommendation.models.User) installed which app (recommendation.models.Item).
Every 6hours you run a script modelcrafter.py (explained bellow) to take this data and represent it as a statistical model.
The statistical model is the heart of the recommender system but in reality it is just bunch of numbers stored as
matrices. These matrices are stored in the database together with original data and used when needed.
When you multiply these matrices in a specific way, you get an estimate how much a user likes an item. As you can
imagine, this model is static and changes only every 6 hours (when you recompute it). 
To make the system more smart and dynamic there are several tricks that we use. 
We implement business logics as filters and rerankers. A filter is a Django module that has logic which items are not good
to recommend. A reranker is a Django module which knows how to modify the scores of the original prediction in order
to implement some logic such as category diversification, i.e., that recommendation list would contain not only games (predicted
by the model) but also some tools, etc.

When you call an API to get recommendations, first the statistical model predicts scores for all applications, then filters
irrelevant items (already installed, shown but never clicked, wrong language) and then applies rerankers. The 
left items with highest scores are returned as a result.

Get Started
-----------

To get started with the Recommendation framework, you first need to set a Django environment. Do all the thing you need
to do in order to start a django project. If you don't now how to do it just check
the `Django <http://djangoproject.com>`_ website and see if it's what you're looking for.

We also use MySQL Database for the project to store the models, applications, etc. 
You need to install standard mysql (5.1) DB server and edit the connection settings in the 'src/firefox/settings.py'
file. When you create the database please use collation: utf8_general_ci.

Next, you will need to install the python module requirements from requirements.txt::

     pip install -r ../requirements.txt 

Installation of the Modules
____________________________

For a moment we have a very manual installation process. This will be replaced with pip style installs any time soon.

1. First you need to add recommendation module to the installed apps in Django settings of the main project:

.. code-block:: python
   :linenos:

   # settings.py

   INSTALLED_APPS = (
        ...  # A ton of cool Django apps
        "recommendation",
        ...
   )


2. Next, you need to create the Django modules using.

.. code-block:: bash
   :linenos:
   
   >>> cd /Users/mumas/devel/ffos/src    
   >>> PYTHONPATH=/Users/mumas/devel/ffos/src/ python manage.py syncdb
    
3. Now you have to fill the database with applications and user data. For the example we use a dummy data
from the data folder. You should replace the path to the real path of the marketplace dumps. For now,
lets start with the dummy data.

.. code-block:: bash
   :linenos:
   
   >>> cd /Users/mumas/devel/ffos/src
   >>> PYTHONPATH=/Users/mumas/devel/ffos/src/ bin/fill_firefox.py items bin/data/app/
   >>> PYTHONPATH=/Users/mumas/devel/ffos/src/ bin/fill_firefox.py users bin/data/user

4. To retrieve recommendations a recommendation model (statistical representation of your data) must be built. 
To have it built you have to run the script:

.. code-block:: bash
   :linenos:

   >>> PYTHONPATH=/Users/mumas/devel/ffos/src/ bin/modelcrafter.py train tensorcofi  # For tensorcofi model
   >>> PYTHONPATH=/Users/mumas/devel/ffos/src/ bin/modelcrafter.py train popularity  # For Popularity

.. note:: This models are static and represent popularity recommendation and tensorCoFi (TF) factor matrix for the user and \
    item population at the moment they are build. Because of that, it doesn't make sense to build any model with no \
    users or items in the database. Also, you will want to rebuild the models once in a while, as the users and items \
    will be added and new connections between user and item are created.
   
In reality, you will need some data about users and items in your system. The popularity model is used when the system has few 
information about a user. And the TF in case that the system has some (>3 apps installed) info about the user. 

This script is shipping with the recommendation framework and builds this matrix. You will want to continue to build
the matrix for new users and items to be included. Keep that in mind.

And voilá, you got your self a recommendation system for your precious little web site. It's a bit static though.

.. code-block:: bash
   :linenos:

   >>> PYTHONPATH=/Users/mumas/devel/ffos/src/ python manage.py runserver
   >>> open firefox at http://127.0.0.1:8000/ 


5. Now you can try to access also the REST API. The full documentation of APIs can be found through the Table of Content.
For example, to generate JSON response just point your web browser to 
http://localhost:8000/api/v2/recommend/5/002c50b7dae6a30ded5372ae1033da43bba90b4d477733375994791e758fbee0.json:


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
            "core": "recommendation.core.TensorCoFiRecommender",
            "filters": [
                "recommendation.filter_owned.filters.FilterOwnedFilter",
                "recommendation.language.filters.SimpleLocaleFilter",
            ],
            "rerankers": [
                "recommendation.records.rerankers.SimpleLogReRanker",
                "recommendation.diversity.rerankers.DiversityReRanker"
            ]
        },
        "logger": "recommendation.decorators.NoLogger"
   }
    
    
Now you have an awesome recommendation system.



