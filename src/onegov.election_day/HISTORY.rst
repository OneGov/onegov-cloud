Changelog
---------

- Fix election and vote template
  [msom]

0.8.0 (2016-08-29)
~~~~~~~~~~~~~~~~~~~

- Adds diagrams to visualize list connections.
  [msom]

- Adds new import formats: Vote/Wabsti, Vote/Internal, Election/Internal.
  [msom]

- Adds the ability to download the SVG images.
  [msom]

- Adds a last update time column to the frontpage and archive pages.
  [msom]

- Shows intermediate results.
  [msom]

- Adds JSON views for results.
  [msom]

- Adds the 'Last-Modified' header to the views with results.
  [msom]

- Adds basic print styles.
  [msom]

- Adds pagination to management views.
  [msom]

- Clears the cache after uploading results.
  [msom]

- Updates French, Romansh and Italian translations.
  [freinhard, msom]

- Sorts the sublists by the ID of the list when displaying list connection
  results of elections.
  [msom]

- Fixes javascript for form dependencies.
  [msom]

- Adds compatibility with Morepath 0.13.
  [href]

0.7.2 (2016-03-18)
~~~~~~~~~~~~~~~~~~~

- Hides candidates list for majorz elections.
  [msom]

- Hides lists for proporz elections.
  [msom]

- Removes color from list bar charts.
  [msom]

- Sorts lists by list id.
  [msom]

- Removes table collapsing for most tables.
  [msom]

- Adds a totals row at the top for tables with totals.
  [msom]

- Folds results to sections.
  [msom]

- Makes title font sizes smaller for mobile devices.
  [msom]

- Adds related links.
  [msom]

0.7.1 (2016-03-14)
~~~~~~~~~~~~~~~~~~~

- Displays visual hints for collapsible tables.
   [msom]

- Adds absolute majority for majorz elections.
  [msom]

0.7.0 (2016-03-11)
~~~~~~~~~~~~~~~~~~~

- Adds elections.
  [msom]

- Adds access to all elections and votes of an election day.
  [msom]

0.6.0 (2016-02-16)
~~~~~~~~~~~~~~~~~~~

- Adds municipality maps for 2016.
  [href]

- Adds "stimmberechtigte" to the columns which may be contain "unbekannt".
  [href]

0.5.3 (2016-02-09)
~~~~~~~~~~~~~~~~~~~

- Ignores invalid years in the url instead of throwing an error.
  [href]

- Adds the ability to indicate lines which should be ignored.
  [href]

- Adds support for open office spreadsheets.
  [href]

0.5.2 (2016-02-08)
~~~~~~~~~~~~~~~~~~~

- Fixes import not working because of an outdated onegov.core dependency.
  [href]

0.5.1 (2016-02-08)
~~~~~~~~~~~~~~~~~~~

- Removes the 'www.' from the base domain.
  [href]

0.5.0 (2016-02-08)
~~~~~~~~~~~~~~~~~~~

- Normalizes the title used as filename in XLSX exports.
  [msom]

- Shows the domain name of the base url instead of the principal name.
  [msom]

- Adds analytics tracking code.
  [msom]

- Allows the select a sheet when importing XLSX files.
  [msom]

0.4.1 (2016-01-12)
~~~~~~~~~~~~~~~~~~~

- No longer caches responses with a status code other than 200.
  [href]

0.4.0 (2016-01-08)
~~~~~~~~~~~~~~~~~~~

- Adds a 5 minute cache for all anonymous pages.
  [href]

- Adds complete french / italian / romansh support.
  [href]

0.3.0 (2015-12-10)
~~~~~~~~~~~~~~~~~~~

- Adds JSON/CSV and XLSX export of all votes.
  [href]

- Shows the votes archive at the bottom of.. the votes archive.
  [gref]

0.2.1 (2015-12-08)
~~~~~~~~~~~~~~~~~~~

- Shows the votes archive at the bottom of each vote.
  [href]

- Shows a helpful error message if a vote exists already.
  [href]

0.2.0 (2015-11-27)
~~~~~~~~~~~~~~~~~~~

- Enables YubiKey integration.
  [href]

0.1.6 (2015-10-26)
~~~~~~~~~~~~~~~~~~~

- Adds accidentally removed 'last change' factoid.
  [href]

- Adds missing translations.
  [href]

0.1.5 (2015-10-26)
~~~~~~~~~~~~~~~~~~~

- Adds XLS/XLSX support.
  [href]

- Improves display of votes with long titles in the manage table.
  [href]

- Fixes display issues with IE9+.
  [href]

- Factoids are now shown for each ballot without being summarized on the vote.
  [href]

- Fixes division by zero error occuring on votes without any results.
  [href]

0.1.4 (2015-10-16)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to leave out uncounted towns in the upload. Missing towns
  are assumed to be uncounted.
  [href]

- Adds internal shortcode for votes.
  [href]

- Improves the design of uncounted votes.
  [href]

- Colors are now always blue if rejected, red if accepted, without exception.
  [href]

- Switch from 'de' to 'de_CH' to properly support Swiss formatting.
  [href]

- Make sure all uploads are aborted if one file fails.
  [href]

- Fix javascript in map when hovering over a lake.
  [href]

0.1.3 (2015-10-12)
~~~~~~~~~~~~~~~~~~~

- Fix upload not allowing for different ballot types initially.
  [href]

0.1.2 (2015-10-12)
~~~~~~~~~~~~~~~~~~~

- Explicitly passes the encoding when reading the yaml file to avoid getting
  the wrong one through the environment.
  [href]

0.1.1 (2015-10-12)
~~~~~~~~~~~~~~~~~~~

- Enables requirements.txt generation on release.
  [href]

0.1.0 (2015-10-12)
~~~~~~~~~~~~~~~~~~~

- Initial Release
