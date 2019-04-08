Onegov Swissvotes
=================

Database for federal votes.

Dataset (CSV, XLSX)
-------------------

The CSV and XLSX version of the dataset are cached on application level and
regenerated only after updating the votes. The files are saved in the root of
the filestorage. Old files are not deleted.

Managing Votes
--------------

Managing votes is done by uploading datasets. Modified votes are automatically
updated and new votes added. Deleting existing votes can be done using the UI.

Full Text Search
----------------

Onegov Swissvotes uses Poppler + Postgres for full text search of attached PDFs.

If you want to reindex the attachments, you can run::

    onegov-swissvotes reindex

Batch Upload Attachments
------------------------

There is a command line command for batch-uploading and indexing attachments::

  onegov-swissvotes import [folder]

The structure of the folder is expected to be in the form::

  [folder]/[attribute]/[locale]/[bfs_number].pdf

The attribute may be any
`LocalizedFile attribute <https://github.com/OneGov/onegov.swissvotes/blob/9c115021547150590b90d185fcdefa151bd98209/onegov/swissvotes/models/vote.py#L644>`_
of the SwissVote model.


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

Onegov Swissvotes follows PEP8 as close as possible. To test for it run::

    tox -e pep8

Onegov Swissvotes uses `Semantic Versioning <http://semver.org/>`_

Build Status
------------

.. image:: https://travis-ci.org/OneGov/onegov.swissvotes.png
  :target: https://travis-ci.org/OneGov/onegov.swissvotes
  :alt: Build Status

Coverage
--------

.. image:: https://coveralls.io/repos/OneGov/onegov.swissvotes/badge.png?branch=master
  :target: https://coveralls.io/r/OneGov/onegov.swissvotes?branch=master
  :alt: Project Coverage

Latest PyPI Release
-------------------

.. image:: https://badge.fury.io/py/onegov.swissvotes.svg
    :target: https://badge.fury.io/py/onegov.swissvotes
    :alt: Latest PyPI Release

License
-------
onegov.swissvotes is released under GPLv2
