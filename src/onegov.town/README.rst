Onegov Town
===========

OneGov web application for small towns.

Run the Tests
-------------
    
Install tox and run it::

    pip install tox
    tox

Limit the tests to a specific python version::

    tox -e py27

Conventions
-----------

Onegov Town follows PEP8 as close as possible. To test for it run::

    tox -e pep8

Onegov Town uses `Semantic Versioning <http://semver.org/>`_

Build Status
------------

.. image:: https://travis-ci.org/OneGov/onegov.town.png
  :target: https://travis-ci.org/OneGov/onegov.town
  :alt: Build Status

Coverage
--------

.. image:: https://coveralls.io/repos/OneGov/onegov.town/badge.png?branch=master
  :target: https://coveralls.io/r/OneGov/onegov.town?branch=master
  :alt: Project Coverage

Latests PyPI Release
--------------------

.. image:: https://badge.fury.io/py/onegov.town.svg
    :target: https://badge.fury.io/py/onegov.town
    :alt: Latest PyPI Release

License
-------
onegov.town is released under GPLv2

Note that Imperavi Redactor (assets/js/redactor.min.js) itself is a proprietary
commercial software, owned by Imperavi. We (Seantis GmbH) bought an OEM license
to distribute Redactor alongside onegov.town, so you may use it for free, but
you are not allowed to use it independently of onegov.town.
