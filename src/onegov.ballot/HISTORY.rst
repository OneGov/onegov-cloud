Changelog
---------

Unreleased
~~~~~~~~~~
0.4.0 (2016-03-07)
~~~~~~~~~~~~~~~~~~~

- Adds models for elections.
  [msom]

0.3.0 (2015-12-15)
~~~~~~~~~~~~~~~~~~~

- Enables translation of the votes title in the database.
  [href]

0.2.0 (2015-12-10)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to create an exportable representation of a vote.
  [href]

0.1.2 (2015-12-08)
~~~~~~~~~~~~~~~~~~~

- If nobody votes on an issue the yeas percentage is now assumed to be 0%.
  Before it was undefined and lead to a division by zero.
  [href]

- Changes the votes order to date, domain, shortcode, title.
  [href]

0.1.1 (2015-10-16)
~~~~~~~~~~~~~~~~~~~

- Adds a last_result_change property on the vote, indicating the last time a
  result was added or changed.
  [href]

- Adds a shortcode to each vote for internal reference.
  [href]

0.1.0 (2015-10-12)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to query the votes by year.
  [href]

- Removes Python 2.x support.
  [href]

0.0.5 (2015-10-06)
~~~~~~~~~~~~~~~~~~~

- Fixes the counts/results/percentages for votes without results.
  [href]

- Yeas/Nays on the vote are no longer simple summations if a counter-proposal
  is present. In this case, the absolute total is taken from the winning
  proposition (say the yeas of the proposal or the counter-proposal, but
  not a merge of the two.).
  [href]

0.0.4 (2015-08-31)
~~~~~~~~~~~~~~~~~~~

- Renames the "yays" to "yeas", the correct spelling.

0.0.3 (2015-06-26)
~~~~~~~~~~~~~~~~~~~

- Remove support for Python 3.3.
  [href]

- Adds support for onegov.core.upgrade.
  [href]

0.0.2 (2015-06-19)
~~~~~~~~~~~~~~~~~~~

- Each ballot result now needs a municipality id, a.k.a BFS-Nummer.
  [href]

0.0.1 (2015-06-18)
~~~~~~~~~~~~~~~~~~~

- Initial Release
