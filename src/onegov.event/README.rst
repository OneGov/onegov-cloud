Onegov Events
=============

Calendar of events for OneGov.

Requirements
------------

This package requires the `HSTORE extension <http://www.postgresql.org/docs/9.4/static/hstore.html>`_

Run the Tests
-------------

Install tox and run it::

    pip install tox
    tox

Limit the tests to a specific python version::

    tox -e py27

Conventions
-----------

Onegov Events follows PEP8 as close as possible. To test for it run::

    tox -e pep8

Onegov Events uses `Semantic Versioning <http://semver.org/>`_

Build Status
------------

.. image:: https://travis-ci.org/OneGov/onegov.event.png
  :target: https://travis-ci.org/OneGov/onegov.event
  :alt: Build Status

Coverage
--------

.. image:: https://coveralls.io/repos/OneGov/onegov.event/badge.png?branch=master
  :target: https://coveralls.io/r/OneGov/onegov.event?branch=master
  :alt: Project Coverage

Latests PyPI Release
--------------------
.. image:: https://img.shields.io/pypi/v/onegov.event.svg
  :target: https://pypi.python.org/pypi/onegov.event
  :alt: Latest PyPI Release

License
-------
onegov.event is released under GPLv2
