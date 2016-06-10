Onegov Form
===========

Common OneGov form library based on WTForms.

Provides fields, widgets and shared form code, as well as the ability to
define custom forms using JSON. Those forms are stored on the database and
are meant to be customer defined forms.

Through the web creating of forms is possible with this, but onegov.form does
not offer any UI to do that.

Run the Tests
-------------

Install tox and run it::

    pip install tox
    tox

Limit the tests to a specific python version::

    tox -e py27

Conventions
-----------

Onegov Form follows PEP8 as close as possible. To test for it run::

    tox -e pep8

Onegov Form uses `Semantic Versioning <http://semver.org/>`_

Build Status
------------

.. image:: https://travis-ci.org/OneGov/onegov.form.png?branch=master
  :target: https://travis-ci.org/OneGov/onegov.form
  :alt: Build Status

Coverage
--------

.. image:: https://coveralls.io/repos/OneGov/onegov.form/badge.png?branch=master
  :target: https://coveralls.io/r/OneGov/onegov.form?branch=master
  :alt: Project Coverage

Latests PyPI Release
--------------------
.. image:: https://img.shields.io/pypi/v/onegov.form.svg
  :target: https://pypi.python.org/pypi/onegov.form
  :alt: Latest PyPI Release

License
-------
onegov.form is released under GPLv2
