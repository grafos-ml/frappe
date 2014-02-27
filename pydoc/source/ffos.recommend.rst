ffos.recommender - FireFox OS Store Recommender
===============================================

This module support the web services for the recommendation system.

Services
--------

.. toctree::
    :maxdepth: 1

    webservice.v2


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
