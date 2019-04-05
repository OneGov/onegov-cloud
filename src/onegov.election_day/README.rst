Onegov Election Day
===================

OneGov ballot results website used on election day.

Ongeov Election Day uses the model from `Onegov Ballot <https://github.com/OneGov/onegov.ballot>`_.


Configuration Options
---------------------

Every Onegov Election Day instance contains a ``principal.yml`` with the following
configuration options:

name
    The name of the principal.

canton or municipality
    The shortcode of the canton or a BFS number of a municipality.

color
    The primary color.

logo
    The filename of the logo.

base
    A link to another site, displayed at the top right of the pages.

analytics
    The JavaScript code for analytics.

use_maps
    Enables or disable maps.

fetch
    Configures fetching results from other principals, see below.

webhooks
    Configures webhook notifications. Expects a list of URLs. Allows to set
    custom HTTP headers.

sms_notication
    Configures SMS notifications. Expects a URL which is used in the SMS.

email_notification
    Enables/disables email notifications.

wabsti_import
    Enables/disables WabstiCExport import.

pdf_signing
    Configures PDF signing. Expects a endpoint URL, user, password and a
    reason.

open_data
    Configures opendata.swiss RDF. Expects an ID, name and mail.


Example::

    name: Govikon
    municipality: 1234
    color: '#ccaa2e'
    logo: 'govikon.svg'
    base: 'https://govikon.gov'
    analytics: "<script type=\\"text/javascript\\"></script>"
    use_maps: false
    fetch:
        lu:
            - federation
            - canton
    webhooks:
        'http://example.org/1':
        'http://example.org/2':
            My-Header: My-Value
    sms_notification: 'https://elections.govikon.ch'
    email_notification: true
    wabsti_import: true
    pdf_signing:
        url: 'http://example.org/3'
        login: user
        password: pass
        reason: election and vote results
    open_data:
        id: govikon
        name: Staatskanzlei Gemeinde Govikon
        mail: info@govikon.ch


Media Generation
----------------

A `Renderer <https://github.com/seantis/d3-renderer>`_ (which renders the D3
scripts) is needed to generate the PDFs and SVGs.

Specify the address of the running server in the YAML, e.g.::

    d3-renderer: 'http://localhost:1337'

And generate the PDFs or SVGs using the CLI::

    onegov-election-day --select /onegov_election_day/* generate-media


Fetching Results from Other Instances
-------------------------------------

Instances running on the same machine can fetch the results from each other.

For example, if we have a cantonal instance and two communal instances, we
can configure them to fetch the results on a domain basis::

  name: Kanton St.Gallen
  canton: sg
  fetch:
    rebstein:
      - municipality
    wil:
      - municipality

  name: Gemeinde Rebstein
  municipality: 3255
  fetch:
    sg:
      - federation
      - canton

  name: Stadt Wil
  municipality: 3427
  fetch:
    sg:
      - federation
      - canton

And then fetch the results using the CLI::

  onegov-election-day --select /onegov_election_day/* fetch



Additional Informations
-----------------------

Informations intended for the end user of a Onegov Election Day instance
(such as upload and downlad format specifications, available JSON and embedded views,
headerless mode, REST interface and WabstiCExport interface) can be found
`here <docs/README.md>`_.

There are also some information regarding `testing the application <docs/testing.md>`_.



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

Onegov Election Day uses `Semantic Versioning <http://semver.org/>`_.


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
