OneGov Server
=============

Serves OneGov applications.

Run the Tests
-------------
    
Install tox and run it::

    pip install tox
    tox

Limit the tests to a specific python version::

    tox -e py27

Conventions
-----------

Onegov Server follows PEP8 as close as possible. To test for it run::

    tox -e pep8

Onegov Server uses `Semantic Versioning <http://semver.org/>`_

Build Status
------------

.. image:: https://travis-ci.org/OneGov/onegov.server.png
  :target: https://travis-ci.org/OneGov/onegov.server
  :alt: Build Status

Coverage
--------

.. image:: https://coveralls.io/repos/OneGov/onegov.server/badge.png?branch=master
  :target: https://coveralls.io/r/OneGov/onegov.server?branch=master
  :alt: Project Coverage

Latests PyPI Release
--------------------
.. image:: https://pypip.in/v/onegov.server/badge.png
  :target: https://crate.io/packages/onegov.server
  :alt: Latest PyPI Release

License
-------
onegov.server is released under GPLv2
