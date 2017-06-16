Changelog
---------

0.6.0 (2017-06-16)
~~~~~~~~~~~~~~~~~~~

- Adds a generic payment property to ticket handlers.
  [href]

0.5.0 (2017-01-03)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to filter the tickets by owner.
  [href]

0.4.1 (2016-06-22)
~~~~~~~~~~~~~~~~~~~

- Removes reaction time from process time (should not be included).
  [href]

0.4.0 (2016-06-22)
~~~~~~~~~~~~~~~~~~~

- Keeps track of the reaction & process time of tickets.
  [href]

0.3.0 (2016-04-14)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to filter by and list the available groups.
  [href]

0.2.1 (2016-01-28)
~~~~~~~~~~~~~~~~~~~

- Uses the latest onegov.core release to get rid of some code.

0.2.0 (2016-01-12)
~~~~~~~~~~~~~~~~~~~

- Adds subtitles to tickets and handlers.
  [href]

0.1.1 (2015-12-16)
~~~~~~~~~~~~~~~~~~~

- State change functions are now idempotent.
  [href]

- Adds a proper exception for invalid state changes.
  [href]

0.1.0 (2015-10-12)
~~~~~~~~~~~~~~~~~~~

- Removes Python 2.x support.
  [href]

0.0.11 (2015-09-28)
~~~~~~~~~~~~~~~~~~~

- FRM-* suggestions now work with and without dash.
  [href]

0.0.10 (2015-09-25)
~~~~~~~~~~~~~~~~~~~

- Load created date undeferred by default.
  [href]

- Adds onegov.search integration.
  [href]

0.0.9 (2015-09-04)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to get tickets of any state from the collection.
  [href]

- Fixes pagination not working.
  [href]

0.0.8 (2015-09-03)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to influence the query used to get the tickets of a
  collection. This can be used to influnce the tickets view for specific
  handlers with custom parameters.
  [href]

0.0.7 (2015-09-01)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to filter the tickets collection by handler.
  [href]

0.0.6 (2015-08-28)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to delete the data behind a handler, creating a snapshot
  before that happens.
  [href]

- The always run upgrade won't show up in the onegov.core upgrade output
  anymore. Eventually we will remove this upgrade task.
  [href]

0.0.5 (2015-07-16)
~~~~~~~~~~~~~~~~~~~

- Reopening a ticket changes its state to pending.
  [href]

0.0.4 (2015-07-15)
~~~~~~~~~~~~~~~~~~~

- Adds a ticket counting function.
  [href]

0.0.3 (2015-07-15)
~~~~~~~~~~~~~~~~~~~

- Adds an email property to the handler.
  [href]

- Adds reopen ticket function.
  [msom]

0.0.2 (2015-07-14)
~~~~~~~~~~~~~~~~~~~

- Adds a handler_id to easily query for a handler record.
  [href]

- Adds accept/close ticket functions.
  [href]

- Adds a ticket collection that supports pagination and filter.
  [href]

0.0.1 (2015-07-10)
~~~~~~~~~~~~~~~~~~~

- Initial Release
