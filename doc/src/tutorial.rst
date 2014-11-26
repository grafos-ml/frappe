.. _tutorial:

=======================
Tutorial for Developers
=======================

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

.. note::

    The raw recommendation come from `test.fm`_ framework. Test.fm is not aware of data origin or mapping. It just
    receives items from 0 to n and users from 0 to m and delivers a list of scores where the index represent the item.
    In order to make this mapping we use SQL id. It starts in 1 so we must decrement 1 for mapping. The same goes for
    user. The incrementation occurs when turning recommendation index to MySQL ids.

Lets take a look at the filter, which removes items already owned by a user from the recommendation list.
The idea is to take an original scores produced by an algorithm (passed as *recommendation*) and modify them
to fit our needs. In this case, the filter traverses the list of items that the user owns and put the lowest 
possible score for that item instead of the original score. We will recommend items with the highest scores,
therefore, these items will not likely be ever recommended.


After finished implementing the filter it must be registered to the system. 
You should edit recommendation.settings.py and modify *RECOMMENDATION_SETTINGS* variable by registering the new filter
with the other filters.

.. code-block:: python
   :linenos:

   # recommendation.settings.py

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


.. _test.fm: https://github.com/grafos-ml/test.fm


Overview of the serving system
------------------------------

While implementing recsys serving engine we had to make some architecture choices.
For example, we do on-line recommendation computations instead of precomputing recommendations
for each user and serving them. This provides flexibility, but limit us on the number
of request per second we can serve. Currently we can respond in reasonable time for catalogue of 50K items.

Here we want to overview the system and explain some design choices. The full documentation will be expanded
in the branch (v3_develop) where implementation will take place.




