Onegov Core
===========

Contains code shared by all OneGov applications.

Run the Tests
-------------
    
Install tox and run it::

    pip install tox
    tox

Limit the tests to a specific python version::

    tox -e py27

Conventions
-----------

Onegov Core follows PEP8 as close as possible. To test for it run::

    tox -e pep8

Onegov Core uses `Semantic Versioning <http://semver.org/>`_

Build Status
------------

.. image:: https://travis-ci.org/OneGov/onegov.core.png
  :target: https://travis-ci.org/OneGov/onegov.core
  :alt: Build Status

Coverage
--------

.. image:: https://coveralls.io/repos/OneGov/onegov.core/badge.png?branch=master
  :target: https://coveralls.io/r/OneGov/onegov.core?branch=master
  :alt: Project Coverage

Latest PyPI Release
-------------------

.. image:: https://badge.fury.io/py/onegov.core.svg
    :target: https://badge.fury.io/py/onegov.core
    :alt: Latest PyPI Release

License
-------
onegov.core is released under GPLv2
