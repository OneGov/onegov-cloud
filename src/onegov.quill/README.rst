Onegov Quill
============

Quill rich text editor integration for OneGov.

Updating Quill.js
-----------------

We use a custom version of Quill.js which adds missing SVGs. Update it with::

    ./build_quill.sh


Run the Tests
-------------

Install tox and run it::

    pip install tox
    tox

Limit the tests to a specific python version::

    tox -e py27

Conventions
-----------

Onegov Quill follows PEP8 as close as possible. To test for it run::

    tox -e pep8

Onegov Quill uses `Semantic Versioning <http://semver.org/>`_

Build Status
------------

.. image:: https://travis-ci.org/OneGov/onegov.quill.png
  :target: https://travis-ci.org/OneGov/onegov.quill
  :alt: Build Status

Coverage
--------

.. image:: https://coveralls.io/repos/OneGov/onegov.quill/badge.png?branch=master
  :target: https://coveralls.io/r/OneGov/onegov.quill?branch=master
  :alt: Project Coverage

Latest PyPI Release
-------------------

.. image:: https://badge.fury.io/py/onegov.quill.svg
    :target: https://badge.fury.io/py/onegov.quill
    :alt: Latest PyPI Release

License
-------
onegov.quill is released under GPLv2
