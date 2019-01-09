Onegov Swissvotes
=================

Database for federal votes.

Run the Tests
-------------

Install tox and run it::

    pip install tox
    tox

Limit the tests to a specific python version::

    tox -e py27

Install jest and run it::

    npm install
    npm t

To update the snapshots, run::

    npm t -- -u


Conventions
-----------

Onegov Swissvotes follows PEP8 as close as possible. To test for it run::

    tox -e pep8

Onegov Swissvotes uses `Semantic Versioning <http://semver.org/>`_

Build Status
------------

.. image:: https://travis-ci.org/OneGov/onegov.swissvotes.png
  :target: https://travis-ci.org/OneGov/onegov.swissvotes
  :alt: Build Status

Coverage
--------

.. image:: https://coveralls.io/repos/OneGov/onegov.swissvotes/badge.png?branch=master
  :target: https://coveralls.io/r/OneGov/onegov.swissvotes?branch=master
  :alt: Project Coverage

Latest PyPI Release
-------------------

.. image:: https://badge.fury.io/py/onegov.swissvotes.svg
    :target: https://badge.fury.io/py/onegov.swissvotes
    :alt: Latest PyPI Release

License
-------
onegov.swissvotes is released under GPLv2
