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


.. _test.fm: https://github.com/grafos-ml/test.fm


Overview of the serving system
------------------------------

General Flow
~~~~~~~~~~~~

While implementing recsys serving engine we had to make some architectural choices.
For example, we do on-line recommendation computations instead of precomputing recommendations
for each user and later serving them. This provides flexibility and possibility to include context, 
but limit us on the number of request per second we can serve. Currently we can respond in 
reasonable time for catalogue of 50K items.

Here we want to give an overview of the more tricky parts of the system, so that the developers
could understand them before diving into the code.

.. image:: scruffy/general-flow.png
    :align: center

The flow diagram above shows the general flow of the information in the frappe system. The Client
(in our case it is someone who uses frappe as a service) asks for a recommendation. Our A/B testing system
selects the module to do recommendations. The Module has predictors, filters and rerankers that
implements core algorithm and business rules around them. Module asks the core algorithm to predict scores
for each item, then asks filters to filter irrelevant recommendations and at the end asks reranker to 
modify scores. The result is returned to the client and is logged to the auditing system.

Module
~~~~~~
.. image:: scruffy/module-class.png
    :align: center

A Module is an object that encapsulates most of the functionality of the recommender system. 
It has predictors such as matrix factorisation that computes scores; aggregator combine these scores
into a vector of scores (one score for one app); filters implement
business logic not to show some of the recommendations, such as apps already owned by the user;
reranker finally modifies the ranked list according to some criteria such as diversity.

.. image:: scruffy/module-flow.png
    :align: center

The flow diagram above
shows an example of how the module processes the recommendations. The filters are fired in a chain just after
the scoring algorithms predicted utility scores for all the items. A reranker is usually quite expensive
to execute and runs last before the result is returned.

The serving system should be fast, therefore, parts of the code is quite optimised. We will speak here optimisations
done for the Matrix Factorisation style recommender. Here to get a score for a user and an item we take a user model
(represented as a vector of floats) and compute a dot product with an item model (also a vector of floats). Because we
want to do it for all the items, we multiply user vector with and item matrix (bunch of vectors). As an output we get
a vector of length the same as the number of items. We do vector matrix multiplication just because it is about 10x 
faster than going one item by one item and computing a dot product. 

Because we use matrices, we have a technical challenge that the indexes for apps should start from 0, and better
there should be no gaps between ids. Now, it looks easy in the beginning, but gets slightly more complicated when
one considers such scenarios:

1. We rebuild models (user and item representations) at different frequencies for different models
2. The item data is dynamic, and some items go away, while others are added
3. Aggregator averages two scoring vectors, therefore these should be of equallength

Id Map
~~~~~~

Or solution to this problems is following:

We store the user and item model as serialised (pickled) python dictionary (see XXX code):

.. code-block:: python
   :linenos:

    {"item1": array([[  6.95231057e-310,   6.95231057e-310,   2.20022438e-314]]),
     "item2": array([[  3.10503618e+231,   3.10503618e+231,   3.10503618e+231]]),
     "item5": array([[  3.10503618e+231,   3.10503618e+231,   2.12199580e-314]])}

This occupies XXX times more on database than saving just array, however, we get flexibility
of having item ids as they appear in the system. Each Module loads all the arrays for each of the
predictor into memory. Next, it constructs a single one-to-one IdMap that maps these string ids, to an internal
integer id. This internal id represents an row in the matrix.

For each of the predictor we construct an item matrix using the IdMap. If some item
is missing in the loaded data, we simply put zeros there. So each model contains consistent
IdMap for all the predictors within the Module. Now, module constructs filters and rerankers
that also are unique for each Module.



