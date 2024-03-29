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

  sudo -u [user] bin/onegov-swissvotes --select /onegov_swissvotes/[instance] import [folder]

The structure of the folder is expected to be in the form::

  [folder]/[attribute]/[locale]/[bfs_number].pdf

The attribute may be any
`LocalizedFile attribute <https://github.com/OneGov/onegov.swissvotes/blob/9c115021547150590b90d185fcdefa151bd98209/onegov/swissvotes/models/vote.py#L644>`_
of the SwissVote model.
