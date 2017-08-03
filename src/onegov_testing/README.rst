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

.. image:: https://travis-ci.org/OneGov/onegov_testing.png
  :target: https://travis-ci.org/OneGov/onegov_testing
  :alt: Build Status

Coverage
--------

.. image:: https://coveralls.io/repos/OneGov/onegov_testing/badge.png?branch=master
  :target: https://coveralls.io/r/OneGov/onegov_testing?branch=master
  :alt: Project Coverage

Latests PyPI Release
--------------------
.. image:: https://pypip.in/v/onegov_testing/badge.png
  :target: https://crate.io/packages/onegov_testing
  :alt: Latest PyPI Release

License
-------
onegov_testing is released under GPLv2
