.. frappe documentation master file

Welcome to Frappe's documentation!
==================================

Frappe is a Django_ application that provides item recommendations for users. The simplest form of recommendations now
are based on collaborative filtering tensor factorisation (TF). We use `test.fm`_ framework for computing the models.
Frappe then implements a logic to use the models in order to serve recommendations. The framework ships with a set of
filters and re-rankers to implement business rules such as diversity. Filters are modules that implement a peace of
logic such as "filter out items that users has already installed", whereas, rerankers implement more complex logic such
as enforcing diversity or discounting values for some items.

The framework was originally designed for Firefox OS marketplace but is flexible enough to adapt to the most of the
application domains. Within the framework it is possible to develop and deploy "recommendation" plugins that improve
the recommendations, make additional business rules, etc.

Project's home
--------------
Check for the latest release of this project on `Github`_.

Please report bugs or ask questions using the `Issue Tracker`_.

Contents
--------

.. toctree::
  :maxdepth: 2

  installation
  tutorial
  demos
  filters
  rerankers
  rest_api
  changelog

.. _Django: https://www.djangoproject.com/
.. _Github: https://github.com/grafos-ml/frappe
.. _Issue Tracker: https://github.com/grafos-ml/frappe/issues
.. _test.fm: https://github.com/grafos-ml/test.fm