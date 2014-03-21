Recommendation Framework
========================

The Recommendation Framework is a Django application that provides item recommendations for users. The simplest form of
recommendations now are based on collaborative filtering tensor matrix. The framework also ships with a set of filters
and re-rankers to give more juice to the recommendation.

REST API
--------

.. toctree::
    :maxdepth: 1

    recommendation.api


Filters
-------

Methods that are design to boost or week the item original score.

User Content Filters
++++++++++++++++++++

.. automodule:: ffos.recommender.filters
   :members: RepetitionFilter, LocaleFilter
   :special-members: __init__, __call__

Re-Ranker
---------

Methods that re-arrange the original recommendation list based on some criteria.

User Content Re-Ranker
++++++++++++++++++++++

.. automodule:: ffos.recommender.filters
   :members: RegionReRanker, CategoryReRanker, RepetitionReRanker
   :special-members: __init__, __call__

Log Based Re-Ranker
+++++++++++++++++++

.. automodule:: ffos.recommender.rlogging.rerankers
   :members:
   :special-members: __init__, __call__

Diversity Re-Ranker
+++++++++++++++++++

.. automodule:: ffos.recommender.diversification
   :members:
   :special-members: __init__, __call__
