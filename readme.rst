.. default-role:: code

Keg Elements
####################


.. image:: https://circleci.com/gh/level12/keg-elements.svg?style=svg
  :target: https://circleci.com/gh/level12/keg-elements

.. image:: https://codecov.io/github/level12/keg-elements/coverage.svg?branch=master
  :target: https://codecov.io/github/level12/keg-elements?branch=master


Keg Elements is the testing ground for ideas and code that will eventually make their way into
`Keg`_ or an official Keg extension.


.. _Keg: https://pypi.python.org/pypi/Keg

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
