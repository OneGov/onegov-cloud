Changelog
---------

0.6.0 (2016-03-22)
~~~~~~~~~~~~~~~~~~~

- Uses a simpler analyzer for autocompletion.

  This change leads to the autocompletion working more literally. That is if
  we enter 'A1', we will find 'A1' and 'A11' but not 'A'. Before, all numbers
  were stripped from the autocompletion which is not what we want because
  we use autocompletion quite lierally (search for FRM-1234-5678 for example).
  [href]

0.5.0 (2016-02-22)
~~~~~~~~~~~~~~~~~~~

- Migrates to latest elasticsearch-dsl release.
  [href]

0.4.0 (2016-02-03)
~~~~~~~~~~~~~~~~~~~

- Adds support for query explanations.
  [href]

0.3.2 (2016-02-02)
~~~~~~~~~~~~~~~~~~~

- Fixes connection pool exhaustion occuring when reindexing many tennants.
  [href]

0.3.1 (2016-01-26)
~~~~~~~~~~~~~~~~~~~

- Keep elasticsearch-dsl below 0.0.9 until there's a release that supports
  elasticsearch 2.0.0.
  [href]

0.3.0 (2016-01-11)
~~~~~~~~~~~~~~~~~~~

- Require elasticsearch 2.1.1 or newer.
  [href]

0.2.0 (2016-01-11)
~~~~~~~~~~~~~~~~~~~

- Pin elasticsearch to 2.1 for now.

  With 2.2 it's no longer possible to support elasticsearch 1.0 and 2.0 with
  2.x. So we have to support either or.

  Currently we support Elasticsearch 1.x. Soon we'll upgrade to 2.x and use
  that exclusively.

  This release is therefore the last release that supports both 1.x and 2.x
  of elasticsearch.
  [href]

0.1.2 (2015-12-22)
~~~~~~~~~~~~~~~~~~~

- Lowers the connection timeout to 5 seconds and uses sniff_on_connection_fail.
  [href]

- Adds compatibility with Elasticsearch 2.1.
  [href]

- Fixes a number of Elasticsearch 2.0 specific bugs.
  [href]

0.1.1 (2015-10-15)
~~~~~~~~~~~~~~~~~~~

- Adds compatibility with Elasticserach 2.0.
  [href]

- Use 'de_CH' translation instead of 'de'.
  [href]

0.1.0 (2015-10-12)
~~~~~~~~~~~~~~~~~~~

- Fixes the delete process failing under certain polymorphic configurations.
  [href]

- Removes Python 2.x support.
  [href]

0.0.7 (2015-09-29)
~~~~~~~~~~~~~~~~~~~

- Catch all significant errors during indexing.
  [href]

0.0.6 (2015-09-28)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to define multiple suggestion inputs per document.
  [href]

- Adds a switch to disable elasticsearch integration.
  [href]

0.0.5 (2015-09-25)
~~~~~~~~~~~~~~~~~~~

- The certificates of elasticsearch hosts are now verified by default.
  [href]

- Adds completion suggestions for search-as-you-type.
  [href]

- Fixes reindex not properly working with onegov.town.
  [href]

0.0.4 (2015-09-22)
~~~~~~~~~~~~~~~~~~~

- Fixes localized mapping not working correctly in certain cases.
  [href]

- Stops the reindex command to create unwanted indices.
  [href]

- Exclude all _source fields by default.
  [href]

- Adds support for polymorphic SQLAlchemy models.
  [href]

- ORM Models now may use any name for their primary key attribute.
  [href]

0.0.3 (2015-09-18)
~~~~~~~~~~~~~~~~~~~

- No longer require elasticsearch to run when configuring the application.
  [href]

0.0.2 (2015-09-18)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to reindex all elasticsearch records.
  [href]

- Fixes a number of issues with the onegov.town integration.
  [href]

0.0.1 (2015-09-17)
~~~~~~~~~~~~~~~~~~~

- Initial Release
