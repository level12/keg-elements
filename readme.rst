.. default-role:: code

Keg Elements
####################


.. image:: https://circleci.com/gh/level12/keg-elements.svg?style=svg
  :target: https://circleci.com/gh/level12/keg-elements

.. image:: https://codecov.io/github/level12/keg-elements/coverage.svg?branch=master
  :target: https://codecov.io/github/level12/keg-elements?branch=master


Keg Elements is a collection of helpers and base classes for building apps with
`Keg`_ or Keg extensions.


.. _Keg: https://pypi.python.org/pypi/Keg


A Simple Example
================

For a simple example and a checklist of sorts for app setup, see the
`Getting Started guide <https://keg-elements.readthedocs.io/en/stable/getting-started.html>`_ in the docs.


Development
===========

To develop on this project, begin by running our tests::

    git clone https://github.com/level12/keg-elements keg-elements-src
    cd keg-elements-src
    tox

You can then examine tox.ini for insights into our development process.  In particular, we:

* use `py.test` for testing (and coverage analysis)
* use `flake8` for linting


Preview Readme
--------------

When updating the readme, use `restview --long-description` to preview changes.


Pre-commit Hooks
----------------

You should install the pre-commit hooks by running ::

    pre-commit install

This will ensure that your code is ready for review.

Issues & Discussion
====================

Please direct questions, comments, bugs, feature requests, etc. to:
https://github.com/level12/keg-elements/issues


Links
=====

* Documentation: https://keg-elements.readthedocs.io/en/stable/index.html
* Releases: https://pypi.org/project/KegElements/
* Code: https://github.com/level12/keg-elements
* Issue tracker: https://github.com/level12/keg-elements/issues
* Keg framework: https://github.com/level12/keg
* Questions & comments: http://groups.google.com/group/blazelibs
