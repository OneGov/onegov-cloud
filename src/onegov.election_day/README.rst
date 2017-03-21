Onegov Election Day
===================

OneGov ballot results website used on election day.

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

Onegov Election Day follows PEP8 as close as possible. To test for it run::

    tox -e pep8

Onegov Election Day uses `Semantic Versioning <http://semver.org/>`_

Media Generation
--------------

A `Renderer <https://github.com/seantis/d3-renderer>`_ (which renders the D3
scripts) is needed to generate the PDFs and SVGs.

Specify the address of the running server in the YAML, e.g.::

    d3-renderer: 'http://localhost:1337'

And generate the PDFs or SVGs using the CLI:

    onegov-election-day --select /onegov_election_day/* generate-media


Build Status
------------

.. image:: https://travis-ci.org/OneGov/onegov.election_day.png?branch=master
  :target: https://travis-ci.org/OneGov/onegov.election_day
  :alt: Build Status

Coverage
--------

.. image:: https://coveralls.io/repos/OneGov/onegov.election_day/badge.png?branch=master
  :target: https://coveralls.io/r/OneGov/onegov.election_day?branch=master
  :alt: Project Coverage

Latests PyPI Release
--------------------
.. image:: https://img.shields.io/pypi/v/onegov.election_day.svg
  :target: https://pypi.python.org/pypi/onegov.election_day
  :alt: Latest PyPI Release

License
-------
onegov.election_day is released under GPLv2
