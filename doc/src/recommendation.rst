Recommendation Framework
========================

The Recommendation Framework is a Django application that provides item recommendations for users. The simplest form of
recommendations now are based on collaborative filtering tensor matrix. The framework also ships with a set of filters
and re-rankers to give more juice to the recommendation.

REST API
--------

.. toctree::
    :maxdepth: 1

    webservice.v2


Filters
-------

Methods that are design to boost or week the item original score.

User Content Filters
++++++++++++++++++++

.. automodule:: recommendation.filter_owned
    :members:
    
.. automodule:: recommendation.language
    :members:
    
Re-Ranker
---------

Methods that re-arrange the original recommendation list based on some criteria.

Log Based Re-Ranker
+++++++++++++++++++

.. automodule:: recommendation.simple_logging
   :members:
