Onegov Gazette
===================

OneGov official notices website.

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

Conventions
-----------

Onegov Gazette follows PEP8 as close as possible. To test for it run::

    tox -e pep8

Onegov Gazette uses `Semantic Versioning <http://semver.org/>`_

Build Status
------------

.. image:: https://travis-ci.org/OneGov/onegov.gazette.png?branch=master
  :target: https://travis-ci.org/OneGov/onegov.gazette
  :alt: Build Status

Coverage
--------

.. image:: https://coveralls.io/repos/OneGov/onegov.gazette/badge.png?branch=master
  :target: https://coveralls.io/r/OneGov/onegov.gazette?branch=master
  :alt: Project Coverage

Latests PyPI Release
--------------------
.. image:: https://img.shields.io/pypi/v/onegov.gazette.svg
  :target: https://pypi.python.org/pypi/onegov.gazette
  :alt: Latest PyPI Release

License
-------
onegov.gazette is released under GPLv2

Note that Imperavi Redactor (assets/js/redactor.min.js) itself is a proprietary
commercial software, owned by Imperavi. We (Seantis GmbH) bought an OEM license
to distribute Redactor alongside onegov.town, so you may use it for free, but
you are not allowed to use it independently of onegov.town.
