Changelog
---------

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
