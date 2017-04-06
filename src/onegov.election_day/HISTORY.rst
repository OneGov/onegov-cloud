Changelog
---------

- Adds support for automatic import of votes using the Wabsti format.
  [msom]

- Hides empty sankey nodes.
  [msom]

- Fixes translations of form error messages.
  [msom]

1.7.4 (2017-04-03)
~~~~~~~~~~~~~~~~~~~

- Adds missing JavaScript library.
  [msom]

1.7.3 (2017-03-31)
~~~~~~~~~~~~~~~~~~~

- Adds sentry support to generate media command.
  [msom]

- Uses touch files instead of file locking for media generation.
  [msom]

1.7.2 (2017-03-31)
~~~~~~~~~~~~~~~~~~~

- Fixes media generator trying to generate empty votes.
  [msom]

1.7.1 (2017-03-30)
~~~~~~~~~~~~~~~~~~~

- Shows app version and link to the changelog in the backend.
  [msom]

1.7.0 (2017-03-29)
~~~~~~~~~~~~~~~~~~~

- Adds PDF and SVG generations.
  [msom]

1.6.1 (2017-03-20)
~~~~~~~~~~~~~~~~~~~

- Improves testing performance.
  [href]

1.6.0 (2017-03-06)
~~~~~~~~~~~~~~~~~~~

- Adds hipchat integration.
  [msom]

- Adds backend link, delete action and pagination for subscribers.
  [msom]

- Displayes the date of the election and vote on the detail view.
  [msom]

- Adds the elected candidates to the JSON summary of an election.
  [msom]

- Adds links to the raw data in the JSON results views of elections and votes.
  [msom]

- Uses colored answers.
  [msom]

- Displays the percentages of intermediate results in the overview, too.
  [msom]

- Fixes displaying the progess of complex votes.
  [msom]

- Fixes displaing tooltips on iOS.
  [msom]

1.5.2 (2017-02-08)
~~~~~~~~~~~~~~~~~~~

- Fixes tests.
  [msom]

1.5.1 (2017-02-08)
~~~~~~~~~~~~~~~~~~~

- Adds (partial) support for 2017.
  [msom]

- Fixes typos in documentation.
  [treinhard, freinhard]

1.5.0 (2017-01-12)
~~~~~~~~~~~~~~~~~~~

- Shows the results of the municipality instead of the overall results for
  federal and cantonal votes in communal instances.
  [msom]

- Adds a column to the party results with the difference of the last two
  percent values.
  [msom]

- Updates translations.
  [msom]

- Changes the order of the result groups in the overview such that communal
  elections and votes are displayed first for communal instances.
  [msom]

1.4.3 (2017-01-04)
~~~~~~~~~~~~~~~~~~~

- Harmonizes the usage of the groups in the various formats.
  [msom]

- Allows to list expats as separate entity (but not using SESAM format).
  [msom]

1.4.2 (2017-01-03)
~~~~~~~~~~~~~~~~~~~

- Fixes cropped labels in panachage charts.
  [msom]

1.4.1 (2016-12-29)
~~~~~~~~~~~~~~~~~~~

- Fixes templates.
  [msom]

1.4.0 (2016-12-28)
~~~~~~~~~~~~~~~~~~~

- Adds panachage charts.
  [msom]

- Adds party results and (comparative) visualisation.
  [msom]

- Uses tabs instead of foldable sections.
  [msom]

- Uses fading effects on charts.
  [msom]

- Changes direction of the list connections sankey chart.
  [msom]

- Displays tooltips inside the map.
  [msom]

- Improves handling of invalid (excel) files.
  [msom]

- Adds (partial) support for 2017.
  [msom]

- Shows the number of SMS subscribers in the manage view.
  [msom]

- Adds support for PyFilesystem 2.x and Chameleon 3.x.
  [href]

1.3.5 (2016-11-23)
~~~~~~~~~~~~~~~~~~~

- Fixes the SMS send command.
  [msom]

1.3.4 (2016-11-23)
~~~~~~~~~~~~~~~~~~~

- Allows the speficify the originator of SMS.
  [msom]

1.3.3 (2016-11-18)
~~~~~~~~~~~~~~~~~~~

- Updates translations.
  [msom]

1.3.2 (2016-11-16)
~~~~~~~~~~~~~~~~~~~

- Updates translations.
  [msom]

1.3.1 (2016-11-16)
~~~~~~~~~~~~~~~~~~~

- Updates translations.
  [msom]

1.3.0 (2016-11-11)
~~~~~~~~~~~~~~~~~~~

- Adds table sorting.
  [msom]

1.2.4 (2016-11-10)
~~~~~~~~~~~~~~~~~~~

- Improves cache handling.
  [msom]

1.2.3 (2016-11-10)
~~~~~~~~~~~~~~~~~~~

- Fixes tests.
  [msom]

1.2.2 (2016-11-10)
~~~~~~~~~~~~~~~~~~~

- Updates texts.
  [msom]

1.2.1 (2016-11-10)
~~~~~~~~~~~~~~~~~~~

- Adds sentry support for SMS queue.
  [msom]

- Adds a simple subscribers view.
  [msom]

1.2.0 (2016-11-10)
~~~~~~~~~~~~~~~~~~~

- Adds SMS notifications.
  [msom]

1.1.3 (2016-11-04)
~~~~~~~~~~~~~~~~~~~

- Hides the footer too when headerless query parameter is set.
  [msom]

1.1.2 (2016-11-03)
~~~~~~~~~~~~~~~~~~~

- Stores the headerless query parameter in the browser session.
  [msom]

1.1.1 (2016-11-02)
~~~~~~~~~~~~~~~~~~~

- Only includes the iFrameResizer if headerless query parameter is set.
  [msom]

1.1.0 (2016-10-31)
~~~~~~~~~~~~~~~~~~~

- Shows the base link everywhere.
  [msom]

- Introduces a headerless query parameter.
  [msom]

- Shows data download links in the primary color.
  [msom]

- Uses darker callout panels.
  [msom]

- Removes archive from election/vote detail views.
  [msom]

- Improves the mobile styling of vote views.
  [msom]

- Displays the number of mandates per list in the bar chart.
  [msom]

- Adds iFrameResizer.
  [msom]

1.0.4 (2016-10-24)
~~~~~~~~~~~~~~~~~~~

- Allow to set custom headers for each webhook.
  [msom]

1.0.3 (2016-09-26)
~~~~~~~~~~~~~~~~~~~

- Fixes upload and view election templates.
  [msom]

1.0.2 (2016-09-26)
~~~~~~~~~~~~~~~~~~~

- Fixes upgrade step running more than once.
  [msom]

1.0.1 (2016-09-26)
~~~~~~~~~~~~~~~~~~~

- Fixes encoding issue in the static data.
  [msom]

1.0.0 (2016-09-26)
~~~~~~~~~~~~~~~~~~~

- Adds support for webhooks.
  [msom]

0.9.5 (2016-09-21)
~~~~~~~~~~~~~~~~~~~

- Adds MIME types typically returned by libmagic for XLS/XLSX files.
  [msom]

0.9.4 (2016-09-21)
~~~~~~~~~~~~~~~~~~~

- Changes the order of backend menu.
  [msom]

0.9.3 (2016-09-19)
~~~~~~~~~~~~~~~~~~~

- Re-release 0.9.2.
  [msom]

0.9.2 (2016-09-19)
~~~~~~~~~~~~~~~~~~~

- Clarify the result of a vote with counter proposal.
  [msom]

- Removes the Last-Modified header from certain views, it interferes with the
  localization.
  [msom]

- Only shows the latest election day on the homepage.
  [msom]

- Adds support for webhooks.
  [msom]

0.9.5 (2016-09-21)
~~~~~~~~~~~~~~~~~~~

- Adds MIME types typically returned by libmagic for XLS/XLSX files.
  [msom]

0.9.4 (2016-09-21)
~~~~~~~~~~~~~~~~~~~

- Changes the order of backend menu.
  [msom]

0.9.3 (2016-09-19)
~~~~~~~~~~~~~~~~~~~

- Re-release 0.9.2.
  [msom]

0.9.2 (2016-09-19)
~~~~~~~~~~~~~~~~~~~

- Clarify the result of a vote with counter proposal.
  [msom]

- Removes the Last-Modified header from certain views, it interferes with the
  localization.
  [msom]

- Fixes bug in folding of proporz election view.
  [msom]

0.9.1 (2016-09-14)
~~~~~~~~~~~~~~~~~~~

- Updates translations.
  [msom]

- Improves print styles.
  [msom]

0.9.0 (2016-09-06)
~~~~~~~~~~~~~~~~~~~

- Adds embed code.
  [msom]

- Updates translations.
  [msom]

- Fixes resize behaviour of charts.
  [msom]

0.8.2 (2016-09-05)
~~~~~~~~~~~~~~~~~~~

- Updates translations.
  [msom]

- Breaks long related links.
  [msom]

- Makes backend tables responsive.
  [msom]

- Adds command line interface to add new instances.
  [msom]

0.8.1 (2016-08-30)
~~~~~~~~~~~~~~~~~~~

- Fixes election and vote templates.
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
