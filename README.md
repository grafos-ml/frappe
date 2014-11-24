[![Build Status](https://travis-ci.org/grafos-ml/frappe.svg?branch=master)](https://travis-ci.org/grafos-ml/frappe)

Installation
============
You can check the official **documentation** [here](http://grafos-ml.github.io/frappe/).

$ pip install https://github.com/grafos-ml/test.fm/archive/v1.0.4.tar.gz

$ pip install frappe

Nosetests
=========
In the package src folder

Django >= 1.7 
$ PYTHONPATH=/project/src runtests (--all | --unit | --integration)

Django = 1.6.*
$ echo yes | ./manage.py test tests/unit/ --with-doctest recommendation/util.py recommendation/core.py recommendation/models.py tests/integration/

Note: Will also nee to configure env variable for database name(FRAPPE_NAME), user(FRAPPE_USER), password(FRAPPE_PASSWORD) and host(FRAPPE_HOST).

Build Documentation
===================
In the package doc folder

$ make html


© 2014 Linas Baltrunas, Joao Baptista, Telefonica Research
