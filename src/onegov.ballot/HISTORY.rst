Changelog
---------

Unreleased
~~~~~~~~~~
1.3.1 (2017-03-30)
~~~~~~~~~~~~~~~~~~~

- Fixes vote model returning integers in some instances.
  [msom]

1.3.0 (2017-03-06)
~~~~~~~~~~~~~~~~~~~

- Adds a function to get the names of the elected candidates.
  [msom]

1.2.2 (2017-02-27)
~~~~~~~~~~~~~~~~~~~

- Return the progress of a vote in relation to its entities, not ballot result
  groups.
  [msom]

1.2.1 (2017-01-10)
~~~~~~~~~~~~~~~~~~~

- Report empty votes as being uncounted.
  [msom]

1.2.0 (2016-12-19)
~~~~~~~~~~~~~~~~~~~

- Adds a model for party results.
  [msom]

1.1.1 (2016-12-09)
~~~~~~~~~~~~~~~~~~~

- Improves the election export.
  [msom]

1.1.0 (2016-11-30)
~~~~~~~~~~~~~~~~~~~

- Adds a model for panachage results.
  [msom]

1.0.3 (2016-11-28)
~~~~~~~~~~~~~~~~~~~

- Fixes handling of changed model relationships.
  [msom]

1.0.2 (2016-11-28)
~~~~~~~~~~~~~~~~~~~

- Changes vote model relationships.
  [msom]

1.0.1 (2016-10-06)
~~~~~~~~~~~~~~~~~~~

- Fixes onegov.ballot not working with SQLAlchemy 1.1.
  [href]

(2016-09-26)
~~~~~~~~~~~~~~~~~~~

- Adds a new domain of influence: municipality.

  **This release includes some breaking changes!**

  The following rows have been renamed:
    - Election.total_municipalities -> Election.total_entities
    - Election.counted_municipalities -> Election.counted_entities
    - ElectionResult.municipality_id -> Election.entity_id
    - BallotResult.municipality_id -> Election.entity_id

  The election and vote exports have changed their columns accordingly.

  [msom]

0.8.0 (2016-08-26)
~~~~~~~~~~~~~~~~~~~

- Orders the collections by date, shortcode and title.
  [msom]

- Returns the yay and nay percentages even though votes have not fully been counted.
  [msom]

0.7.0 (2016-07-06)
~~~~~~~~~~~~~~~~~~~

- Adds pagination to collections.
  [msom]

0.6.1 (2016-07-04)
~~~~~~~~~~~~~~~~~~~

- Changes the behaviour of the last_result_change function to include the last
  change of the election/vote, too.
  [msom]

0.6.0 (2016-06-23)
~~~~~~~~~~~~~~~~~~~

- Adds the number of allocated mandates to the list connection model.
  [msom]

0.5.0 (2016-06-10)
~~~~~~~~~~~~~~~~~~~

- Adds more information to the election export.
  [msom]

0.4.2 (2016-03-17)
~~~~~~~~~~~~~~~~~~~

- Adds meta columns for elections and votes.
  [msom]

- Allows duplicate election and vote titles.
  [msom]

0.4.1 (2016-03-14)
~~~~~~~~~~~~~~~~~~~

- Adds absolute majority for majorz elections.
  [msom]

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
  [href]

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
