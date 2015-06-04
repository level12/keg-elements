.. default-role:: code

Keg Elements
####################


.. image:: https://travis-ci.org/level12/keg.svg?branch=master
    :target: https://travis-ci.org/level12/keg-elements

.. image:: https://coveralls.io/repos/level12/keg/badge.svg?branch=master
    :target: https://coveralls.io/r/level12/keg-elements?branch=master

Keg Elements is the testing ground for ideas and code that will eventually make their way into
`Keg`_ or an official Keg extension.


.. _Keg: https://pypi.python.org/pypi/Keg

Development (Not ready yet, currently no tests)
===============

To develop on this project, begin by running our tests::

    git clone https://github.com/level12/keg-elements keg-elements-src
    cd keg-elements-src
    tox

You can then examine tox.ini for insights into our development process.  In particular, we:

* use `py.test` for testing (and coverage analysis)
* use `flake8` for linting
* store `pip` requirements files in `requirements/`
* cache wheels in `requirements/wheelhouse` for faster & more reliable CI builds

Dependency Management
---------------------

Adding a dependency involves:

#. If it's a run-time dependency, add to `setup.py`.
#. Adding the dependency to one of the requirements files in `requirements/`.
#. Running `requirements/build-wheelhouse.py`.

Preview Readme
--------------

When updating the readme, use `restview --long-description` to preview changes.


Issues & Discussion
====================

Please direct questions, comments, bugs, feature requests, etc. to:
https://github.com/level12/keg-elements/issues

Current Status
==============

Very Alpha, expect changes.

