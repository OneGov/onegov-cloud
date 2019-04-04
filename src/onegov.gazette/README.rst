Onegov Gazette
===================

OneGov official notices website.

Ongeov Gazette uses the model from `Onegov Notice <https://github.com/OneGov/onegov.notice>`_.

Configuration Options
---------------------

Every Onegov Gazette instance contains a ``principal.yml`` with the following
configuration options:

name
    The name of the principal.

color
    The primary color.

logo
    The filename of the logo.

logo_for_pdf
    The filename of the logo used in the PDF.

canton
    The shortcode of the canton, used for the SOGC import.

time_zone
    The timezone used for dates.

help_link
    A link to a help page, displayed in the foooter.

publishing
    Enables the `publish <https://github.com/OneGov/onegov.notice/>`_ state.

frontend
    Enables the frontend.

on_accept
    Allows to send an email in case a notice has been accepted.

sogc_import
    Configures the SOGC import.

Example::

    name: Govikon
    color: '#ccaa2e'
    logo: 'govikon.svg'
    logo_for_pdf: 'govikon-bw.svg'
    canton: 'zg'
    help_link: 'https://help.me/please'
    timezone: 'Europe/Zurich'
    publishing: False
    frontend: False
    on_accept:
        mail_to: 'publisher@govikon.ch'
        mail_from: 'gazette@govikon.ch'
    sogc_import:
        endpoint: 'https://amtsblattportal.ch/api/v1'
        organization: '190'
        category: '126'

Data Import
-----------

There are CLI commands for importing XLSX files containing editors,
organizations, categories and issues::

    onegov-gazette import-editors ...
    onegov-gazette import-organizations ...
    onegov-gazette import-categories ...
    onegov-gazette import-issues ...

There is a CLI command for importing from the SOGC::

    onegov-gazette import-sogc ...

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
