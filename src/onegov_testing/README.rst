Onegov Testing
==============

Contains testing code shared by all OneGov Cloud applications.

Run the Tests
-------------
    
Install tox and run it::

    pip install tox
    tox

Limit the tests to a specific python version::

    tox -e py27

Conventions
-----------

Onegov Testing follows PEP8 as close as possible. To test for it run::

    tox -e pep8

Onegov Testing uses `Semantic Versioning <http://semver.org/>`_

Build Status
------------

.. image:: https://travis-ci.org/OneGov/onegov.testing.png
  :target: https://travis-ci.org/OneGov/onegov.testing
  :alt: Build Status

Coverage
--------

.. image:: https://coveralls.io/repos/OneGov/onegov.testing/badge.png?branch=master
  :target: https://coveralls.io/r/OneGov/onegov.testing?branch=master
  :alt: Project Coverage

Latests PyPI Release
--------------------
.. image:: https://pypip.in/v/onegov.testing/badge.png
  :target: https://crate.io/packages/onegov.testing
  :alt: Latest PyPI Release

License
-------
onegov.testing is released under GPLv2
