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

Note: Will also need to configure env variable for:
 - FRAPPE_NAME for database name
 - FRAPPE_USER for user
 - FRAPPE_PASSWORD for password
 - FRAPPE_HOST for host

Build Documentation
===================
In the package doc folder

$ make html


© 2014 Linas Baltrunas, Joao Baptista, Telefonica Research
