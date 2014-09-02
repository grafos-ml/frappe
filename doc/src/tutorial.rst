.. _tutorial:

========
Tutorial
========

Make a filter
-------------

A filter is a callable class that transform the recommendation in some way.

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

Here is an example for a filter. This filter go for the items that the user own and put the score as low as it can.
After finish the filter it must be registered. In settings you should register it with the other filters on
RECOMMENDATION_SETTINGS.

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