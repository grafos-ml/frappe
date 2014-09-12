.. _tutorial:

========
Tutorial
========

Make a filter
-------------

A filter is a callable class that can be used to implement a business logic to filter out irrelevant recommendations.
Filters are executed after a recommendation model (such as Collaborative Filtering) made user-item utility score predictions.

.. code-block:: python
   :linenos:

   class SomeFilter(object):

        def __call__(self, user, recommendation, size):
            """

            :param user: An recommendation.models.User instance for the user that ask for the recommendation.
            :param recommendation: An numpy.array with shape (n,) being n the number of items in the system.
                The index of the array should represent the id for the item in the database and the value a
                score in witch the recommendation will be evaluated.
            :param size: The size of the recommendation asked.
            """
            for item in user.owned_items:
                recommendation[item.pk-1] = float("-inf")
            return recommendation

Lets take a look at the filter, which removes items already owned by a user from the recommendation list.
The idea is to take an original scores produced by an algorithm (passed as *recommendation*) and modify them
to fit our needs. In this case, the filter traverses the list of items that the user owns and put the lowest 
possible score for that item instead of the original score. We will recommend items with the highest scores,
therefore, these items will not likely be ever recommended.


After finished implementing the filter it must be registered to the system. 
You should edit settings.py and modify *RECOMMENDATION_SETTINGS* variable by registering the new filter
with the other filters.

.. code-block:: python
   :linenos:

   # settings.py

   RECOMMENDATION_SETTINGS = {
        "default": {
            "core": "recommendation.core.TensorCoFiController",
            "filters": [] if TESTING_MODE else [
                ...
                "some_package.filters.SomeFilter",
                ...
                ],
            "rerankers": [
                ...
            ]
        },
        "logger": "recommendation.simple_logging.decorators.LogEvent"
    }

.. note::

    If your filter is build in a django app and is dependent of a model of that app, you must include the app in
    the installed apps and syncdb or make sure the proper tables exist. The same goes for other django specific like
    middlewares, cache, etc...