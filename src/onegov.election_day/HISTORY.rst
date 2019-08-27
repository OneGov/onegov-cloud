Changelog
---------
3.13.9 (2019-08-19)
~~~~~~~~~~~~~~~~~~~

- Fixes import error
  [dadadamotha]
- Refactoring of error handling to have more consistency and code-reuse

3.13.8 (2019-08-09)
~~~~~~~~~~~~~~~~~~~

- Fixes import error of majorz election test dataset and improves error messages for wabstiC import.
  [dadadamotha]


3.13.7 (2019-07-22)
~~~~~~~~~~~~~~~~~~~

- Adds WabstiC v2.3 (2018) support.
  [dadadamotha]

3.13.6 (2019-05-28)
~~~~~~~~~~~~~~~~~~~

- Fixes tests failing with latest babel release.
  [href]

3.13.5 (2019-05-07)
~~~~~~~~~~~~~~~~~~~

- Fixes expats not displayed for temporary results.
  [msom]

3.13.4 (2019-04-30)
~~~~~~~~~~~~~~~~~~~

- Removes legacy sentry parameter.
  [msom]

3.13.3 (2019-04-30)
~~~~~~~~~~~~~~~~~~~

- Enables sentry in CLI commands.
  [msom]

- Replaces Raven JS with Sentry.
  [msom]

3.13.2 (2019-04-29)
~~~~~~~~~~~~~~~~~~~

- Refactors send SMS command.
  [msom]

3.13.1 (2019-04-29)
~~~~~~~~~~~~~~~~~~~

- Removes sentry integration.
  [msom]

3.13.0 (2019-04-23)
~~~~~~~~~~~~~~~~~~~

- Adds more informations to the election and election compound JSON views.
  [msom]

- Shows the districts instead of the election titles in all election compound
  views.
  [msom]

- Uses static URLs for embedded ballot views.
  [msom]

3.12.1 (2019-04-16)
~~~~~~~~~~~~~~~~~~~

- Update translations.
  [msom]

3.12.0 (2019-04-12)
~~~~~~~~~~~~~~~~~~~

- Optimizes interal and WabstiC imports.
  [msom]

3.11.0 (2019-04-05)
~~~~~~~~~~~~~~~~~~~

- Allows to manage upload tokens using the web UI.
  [msom]

- Uses a dropdown for the election and election compound manage menu entries.
  [msom]

- Shows more infos about elections and votes in forms.
  [msom]

- Uses the chosen select widgets in various forms.
  [msom]

3.10.0 (2019-03-18)
~~~~~~~~~~~~~~~~~~~

- Adds mandate allocation view to election compound.
  [msom]

- Fixes party results possibly not being downloadable.
  [msom]

- Fixes party results possibly included in the PDF.
  [msom]

3.9.4 (2019-03-14)
~~~~~~~~~~~~~~~~~~~

- Uses yamls safe load function.
  [msom]

3.9.3 (2019-03-11)
~~~~~~~~~~~~~~~~~~~

- Fixes JavaScript race conditions.
  [msom]

- Updates JavaScript libraries.
  [msom]

3.9.2 (2019-03-06)
~~~~~~~~~~~~~~~~~~~

- Fixes outer join ambiguity in SQL statement.
  [href]

3.9.1 (2019-02-10)
~~~~~~~~~~~~~~~~~~~

- Fixes CSV templates.
  [msom]

3.9.0 (2019-01-24)
~~~~~~~~~~~~~~~~~~~

- Adds final mapdata for 2019.
  [msom]

- Adds a configuration option to elections and votes to use/ignore expats
  results during upload.
  [msom]

- Updates the WabstiCExport (proporz) import to the latest version.
  [msom]

- Fixes expats in maps not getting updated on change.
  [msom]

3.8.2 (2019-01-21)
~~~~~~~~~~~~~~~~~~~

- Fixes the calculation of the candidates percentages by entity and district.
  [msom]

3.8.1 (2019-01-18)
~~~~~~~~~~~~~~~~~~~

- Hides the absolute majority for intermediate results.
  [msom]

3.8.0 (2018-12-20)
~~~~~~~~~~~~~~~~~~~

- Adds municipalities and quarter data for 2019.
  [msom]

- Adds interim map data for 2019.
  [msom]

3.7.4 (2018-11-27)
~~~~~~~~~~~~~~~~~~~

- Adds a configuration option to enable/disable party strengths of election
  compounds.
  [msom]

3.7.3 (2018-11-25)
~~~~~~~~~~~~~~~~~~~

- Removes XLSX data format from suggested citations.
  [msom]

3.7.2 (2018-11-05)
~~~~~~~~~~~~~~~~~~~

- Updates translations.
  [msom]

3.7.1 (2018-11-05)
~~~~~~~~~~~~~~~~~~~

- Uses a more specific summarized email subject.
  [msom]

3.7.0 (2018-11-02)
~~~~~~~~~~~~~~~~~~~

- Adds summarized notifications.
  [msom]

3.6.10 (2018-10-11)
~~~~~~~~~~~~~~~~~~~

- Fixes party panachage results being added for parties only being present
  in former elections.
  [msom]

3.6.9 (2018-09-25)
~~~~~~~~~~~~~~~~~~~

- Updates the WabstiCExport (majorz, vote) import to the latest version.
  [msom]

3.6.8 (2018-09-19)
~~~~~~~~~~~~~~~~~~~

- Makes the WabstiCExport (majorz) import more robust.
  [msom]

3.6.7 (2018-09-19)
~~~~~~~~~~~~~~~~~~~

- Uses the phone number field from onegov.form.
  [msom]

3.6.6 (2018-09-19)
~~~~~~~~~~~~~~~~~~~

- Moves the phone number validator to onegov.form.
  [msom]

3.6.5 (2018-08-20)
~~~~~~~~~~~~~~~~~~~

- Fixes the election template.
  [msom]

3.6.4 (2018-08-20)
~~~~~~~~~~~~~~~~~~~

- Displays elections withouth candidacies correctly.
  [msom]

3.6.3 (2018-07-19)
~~~~~~~~~~~~~~~~~~~

- Lists elected candidates and lists with mandates first in the heatmaps.
  [msom]

- Fixes tab menu dropdown styling.
  [msom]

3.6.2 (2018-07-11)
~~~~~~~~~~~~~~~~~~~

- Fixes absolute majority field beeing visible when editing proporz elections.
  [msom]

- Reorganizes the menus.
  [msom]

3.6.1 (2018-07-06)
~~~~~~~~~~~~~~~~~~~

- Fixes percentages of votes aggregations.
  [msom]

3.6.0 (2018-07-05)
~~~~~~~~~~~~~~~~~~~

- Adds vote views for districts.
  [msom]

- Adds entities and districts heatmaps for candidates and lists.
  [msom]

- Fixes throwing an error on unexpected principal configuration options.
  [msom]

3.5.9 (2018-06-19)
~~~~~~~~~~~~~~~~~~~

- Add compatibility with wtforms 2.2.
  [msom]

3.5.8 (2018-06-18)
~~~~~~~~~~~~~~~~~~~

- Fixes importing XLSX files with only one column not working.
  [msom]

3.5.7 (2018-06-11)
~~~~~~~~~~~~~~~~~~~

- Prefills the email when unsubscribing from the newsletter.
  [msom]

- Updates javascript libraries.
  [msom]

- Fixes table sorting.
  [msom]

3.5.6 (2018-06-08)
~~~~~~~~~~~~~~~~~~~

- Make wabsti (majorz) import more robust.
  [msom]

3.5.5 (2018-06-04)
~~~~~~~~~~~~~~~~~~~

- Removes the radius from the panels.
  [msom]

3.5.4 (2018-06-04)
~~~~~~~~~~~~~~~~~~~

- Fixes placing of the expats/globe tooltip.
  [msom]

- Fixes sankey chart trying to render empty nodes and links.
  [msom]

3.5.3 (2018-06-04)
~~~~~~~~~~~~~~~~~~~

- Improves responsive behaviour.
  [msom]

3.5.2 (2018-05-29)
~~~~~~~~~~~~~~~~~~~

- Hides related elections title if empty.
  [msom]

3.5.1 (2018-05-29)
~~~~~~~~~~~~~~~~~~~

- Adds compatibility with babel 2.6.
  [msom]

3.5.0 (2018-05-17)
~~~~~~~~~~~~~~~~~~~

- Allows to add related elections to elections.
  [msom]

- Allows to specify the majority type of a majorz election.
  [msom]

3.4.7 (2018-05-15)
~~~~~~~~~~~~~~~~~~~

- Adds the node titles to the sankey links.
  [msom]

- Uses 'mandates' for propoz elections, 'seats' for majorz elections.
  [msom]

3.4.6 (2018-05-07)
~~~~~~~~~~~~~~~~~~~

- Updates translations.
  [msom]

- Orders the list panachage nodes by alphabet (if possible).
  [msom]

3.4.5 (2018-04-26)
~~~~~~~~~~~~~~~~~~~

- Adds an option to allow regional elections to span over several districts.
  [msom]

- Improve wabsti import.
  [msom]

3.4.4 (2018-04-24)
~~~~~~~~~~~~~~~~~~~

- Adds CORS header to JSON views.
  [msom]

- Runs the CLI tests in a separate process.
  [msom]

- Improves the import when using the internal format.
  [msom]

3.4.3 (2018-04-13)
~~~~~~~~~~~~~~~~~~~

- Removes XLSX export.
  [msom]

- Fixes district/entity not shown in election compounds PDF.
  [msom]

- Uses a fixed callout color.
  [msom]

- Adds titles to emails.
  [msom]

3.4.2 (2018-04-10)
~~~~~~~~~~~~~~~~~~~

- Fixes district/entity not shown in election compounds.
  [msom]

- Improves performance.
  [msom]

3.4.1 (2018-04-09)
~~~~~~~~~~~~~~~~~~~

- Updates translations.
  [msom]

- Adds map data of ZG 2004-2012.
  [msom]

- Fixes PDF styles.
  [msom]

- Fixes pages cache.
  [msom]

3.4.0 (2018-03-29)
~~~~~~~~~~~~~~~~~~~

- Adds support for parties panachage.
  [msom]

- Adds support for colorized sankey charts.
  [msom]

3.3.0 (2018-03-26)
~~~~~~~~~~~~~~~~~~~

- Adds election compounds PDFs.
  [msom]

- Redesign the party strengths view.
  [msom]

3.2.1 (2018-03-20)
~~~~~~~~~~~~~~~~~~~

- Includes a distinct ID the party results export.
  [msom]

3.2.0 (2018-03-19)
~~~~~~~~~~~~~~~~~~~

- Adds party results to election compounds.
  [msom]

- Improves display of tables.
  [msom]

- Optimizes some views.
  [msom]

3.1.1 (2018-03-13)
~~~~~~~~~~~~~~~~~~~

- Adjusts the custom wabsti import files.
  [msom]

3.1.0 (2018-03-13)
~~~~~~~~~~~~~~~~~~~

- Adds election compounds.
  [msom]

3.0.0 (2018-03-08)
~~~~~~~~~~~~~~~~~~~

- Harmonizes the progress implementation of elections and votes.
  [msom]

- Supports regional elections.
  [msom]

- Uses seperate domain definitions for elections and votes in the principals.
  [msom]

- Uses the static data to detect if a principal has districts or not.
  [msom]

- Uses a single function to import wabsti majorz elections.
  [msom]

- Improves handling of wabsti exporter formats.
  [msom]

- Fixes spelling of "eligible voters".
  [msom]

  **Breaking changes: The import and export formats have changed!**

  - ``election_counted_entities`` and ``election_total_entitites`` have been
    replaced with a ``counted`` column
  - ``elegible_voters`` have been renamed to ``eligible_voters``

2.1.1 (2018-03-06)
~~~~~~~~~~~~~~~~~~~

- Optimizes sending email notifications.
  [msom]

- Splits e-mails into transactional/marketing.
  [href]

- Makes some columns of the wabsti vote format optional.
  [msom]

2.1.0 (2018-03-05)
~~~~~~~~~~~~~~~~~~~

- Adds zulip integration.
  [msom]

2.0.2 (2018-02-01)
~~~~~~~~~~~~~~~~~~~

- Uses a more generic PDF signing error log entry.
  [msom]

- Fixes media generation removing the lock file of other instances.
  [msom]

2.0.1 (2018-01-29)
~~~~~~~~~~~~~~~~~~~

- Adds mapdata for 2018.
  [msom]

2.0.0 (2018-01-23)
~~~~~~~~~~~~~~~~~~~

- Splits the group of an entity into a name and a district.
  [msom]

- Use the static data for entity names and districts.
  [msom]

- Display districts as a separate column.
  [msom]

- Adds district translations.
  [msom]

- Makes principal polymorphic.
  [msom]

1.19.9 (2018-01-16)
~~~~~~~~~~~~~~~~~~~

- Requires that the title translations of election and votes for the default
  locale is provided.
  [msom]

- Improves title translations fallbacks.
  [msom]

- Updates translations.
  [msom]

1.19.8 (2018-01-11)
~~~~~~~~~~~~~~~~~~~

- Adds compatibility with latest onegov.pdf.
  [msom]

1.19.7 (2018-01-09)
~~~~~~~~~~~~~~~~~~~

- Updates translations.
  [msom]

- Localizes notification mails.
  [msom]

1.19.6 (2018-01-04)
~~~~~~~~~~~~~~~~~~~

- Adds static data for 2018.
  [msom]

1.19.5 (2018-01-04)
~~~~~~~~~~~~~~~~~~~

- Skips test_principal_districts due to missing 2018 maps.
  [href]

- Requires Python 3.6.
  [href]

1.19.4 (2017-12-22)
~~~~~~~~~~~~~~~~~~~

- Switches to onegov core's custom json module.
  [href]

1.19.3 (2017-12-21)
~~~~~~~~~~~~~~~~~~~

- Updates translations.
  [msom]

1.19.2 (2017-12-18)
~~~~~~~~~~~~~~~~~~~

- Fixes notification mail percentages for complex votes.
  [msom]

1.19.1 (2017-12-18)
~~~~~~~~~~~~~~~~~~~

- Fixes mail notification reply to address.
  [msom]

- Fixes notification options not working.
  [msom]

- Adds missing translation.
  [msom]

1.19.0 (2017-12-18)
~~~~~~~~~~~~~~~~~~~

- Adds email alerts.
  [msom]

1.18.1 (2017-12-04)
~~~~~~~~~~~~~~~~~~~

- Updates translations.
  [msom]

1.18.0 (2017-12-01)
~~~~~~~~~~~~~~~~~~~

- Adds tacit elections.
  [msom]

- Improves calculation of last changes.
  [msom]

- Provides open data citation examples.
  [msom]

1.17.1 (2017-11-28)
~~~~~~~~~~~~~~~~~~~

- Fix changelog.
  [msom]

1.17.0 (2017-11-28)
~~~~~~~~~~~~~~~~~~~

- Adds titles for counter-proposal and tie-breakers.
  [msom]

1.16.0 (2017-11-27)
~~~~~~~~~~~~~~~~~~~

- Allows to clear the results of elections and votes.
  [msom]

- Always Show First and Last Item of Pagination.
  [msom]

- Adds missing title slot.
  [msom]

- Uses onegov.pdf.
  [msom]

- Uses a confirmation form for updating results.
  [msom]

1.15.10 (2017-10-23)
~~~~~~~~~~~~~~~~~~~~

- Updates RavenJs to 3.19.1.
  [msom]

1.15.9 (2017-09-20)
~~~~~~~~~~~~~~~~~~~

- Fixes placing of terms of use.
  [msom]

1.15.8 (2017-09-14)
~~~~~~~~~~~~~~~~~~~

- Fixes upload of wabsti files.
  [msom]

1.15.7 (2017-08-29)
~~~~~~~~~~~~~~~~~~~

- Fixes test failing due to changes in the memory backend.
  [msom]

1.15.6 (2017-08-25)
~~~~~~~~~~~~~~~~~~~

- Sorts the elections/votes by issue date in the open data view.
  [msom]

1.15.5 (2017-08-17)
~~~~~~~~~~~~~~~~~~~

- Uses latest onegov.user.
  [msom]

1.15.4 (2017-08-08)
~~~~~~~~~~~~~~~~~~~

- Updates translations.
  [msom]

1.15.3 (2017-08-03)
~~~~~~~~~~~~~~~~~~~

- Fixes the open data description translations.
  [msom]

1.15.2 (2017-07-17)
~~~~~~~~~~~~~~~~~~~

- Adds an open data licence / terms of use.
  [msom]

- Excludes XLSX from the opendata catalog.
  [msom]

- Uses the date of the election/vote for the opendata issue date.
  [msom]

- Uses a better description of the elections/vote in the opendata catalog.
  [msom]

1.15.1 (2017-07-03)
~~~~~~~~~~~~~~~~~~~

- Fixes archived results reporting wrong schema.
  [msom]

1.15.0 (2017-06-29)
~~~~~~~~~~~~~~~~~~~

- Supports wabsti files for municipalities (votes, majorz elections).
  [msom]

- Allows to upload UTF-16 wabsti files.
  [msom]

- Fixes showing the wrong last change date.
  [msom]

- Updates translations.
  [msom]

1.14.1 (2017-06-23)
~~~~~~~~~~~~~~~~~~~

- Fixes searching an inexisting subscriber throwing an error.
  [msom]

- Improves error reporting when sending SMS.
  [msom]

1.14.0 (2017-06-23)
~~~~~~~~~~~~~~~~~~~

- Adds password reset function.
  [msom]

- Sends a confirmation SMS when subscribing.
  [msom]

- Adds status to SMS notifications.
  [msom]

- Exports all translations of the titles.
  [msom]

- Renders the open data JSON with pretty print and with a meaningful file name.
  [msom]

- Switches the header logo and base link.
  [msom]

- Adds tests.
  [msom]

1.13.2 (2017-06-21)
~~~~~~~~~~~~~~~~~~~

- Fixes ambiguous translation.
  [msom]

- Fixes smaller bugs in import functions.
  [msom]

- Drops SESAM support.
  [msom]

- Updates tests.
  [msom]

1.13.1 (2017-06-15)
~~~~~~~~~~~~~~~~~~~

- Specify the CSV dialect of our own files to avoid guessing the wrong one.
  [msom]

1.13.0 (2017-06-15)
~~~~~~~~~~~~~~~~~~~

- Adds a REST interface to upload internal formats.
  [msom]

- Returns parties CSV exports as files, too.
  [msom]

1.12.2 (2017-06-13)
~~~~~~~~~~~~~~~~~~~

- Adds map data of SG for 2004-2012.
  [msom]

- Fixes ballot map scaling of legend and expats globe.
  [msom]

1.12.1 (2017-06-12)
~~~~~~~~~~~~~~~~~~~

- Caches catalog view.
  [msom]

- Fixes wrong email address in opendata.swiss catalog.
  [msom]

1.12.0 (2017-06-09)
~~~~~~~~~~~~~~~~~~~

- Adds support for opendata.swiss.
  [msom]

- Returns CSV exports as files.
  [msom]

- Fixes grouped bar chart.
  [msom]

1.11.3 (2017-06-07)
~~~~~~~~~~~~~~~~~~~

- Fixes failing upgrade steps.
  [msom]

1.11.2 (2017-06-07)
~~~~~~~~~~~~~~~~~~~

- Fixes tests.
  [msom]

1.11.1 (2017-06-07)
~~~~~~~~~~~~~~~~~~~

- Improves the status callouts.
  [msom]

- Makes the footer more visually more distinguishable from the content.
  [msom]

- Fixes failing upgrade steps.
  [msom]

1.11.0 (2017-06-06)
~~~~~~~~~~~~~~~~~~~

- Adds PDF signing.
  [msom]

- Parses the party of candidates and displays them for majorz elections.
  [msom]

- Improves party results.
  [msom]

- Shows the progress bar of the current ballot.
  [msom]

- Shows the modification date of elections and votes in the detail view and
  the PDF.
  [msom]

1.10.1 (2017-05-31)
~~~~~~~~~~~~~~~~~~~

- Improves performance of generating media.
  [msom]

1.10.0 (2017-05-29)
~~~~~~~~~~~~~~~~~~~

- Adds static data for 2002-2008.
  [msom]

- Indicates the current archive page in the listing.
  [msom]

- Changes back to election day link to breadcrumbs.
  [msom]

- Hides the subscribe/unsubscribe form after form submission.
  [msom]

- Centers the header for small sizes.
  [msom]

- Allows to upload votes when no map data is available.
  [msom]

- Gets the entity names from the static data when uploading wabsti votes.
  [msom]

- Makes wabsti uploading more robust.
  [msom]

- Fixes parsing of empty votes when uploading complex wabsti votes.
  [msom]

1.9.0 (2017-05-22)
~~~~~~~~~~~~~~~~~~~

- Adds manage subscription search function.
  [msom]

- Removes the districs view of majorz elections.
  [msom]

- Hides results of empty votes (in any case).
  [msom]

- Ignores expats with no eligible voters when uploading Wabsti vote results.
  [msom]

- Ignores uncounted entities when uploading WabstiCExport vote results.
  [msom]

- Deletes superfluous ballots when uploading vote results.
  [msom]

- Fixes the phone number placeholder in subscriber form.
  [msom]

- Fixes importing of expats (vote/internal).
  [msom]

- Fixes format description link.
  [msom]

1.8.15 (2017-05-19)
~~~~~~~~~~~~~~~~~~~

- Fixes parsing of empty votes when uploading WabstiCExport files.
  [msom]

1.8.14 (2017-05-18)
~~~~~~~~~~~~~~~~~~~

- Fixes typo.
  [msom]

1.8.13 (2017-05-15)
~~~~~~~~~~~~~~~~~~~

- Fixes ballot map hovering issue.
  [msom]

1.8.12 (2017-05-15)
~~~~~~~~~~~~~~~~~~~

- Adds exception views.
  [msom]

- Fixes height of maps in embedding code.
  [msom]

1.8.11 (2017-05-11)
~~~~~~~~~~~~~~~~~~~

- Fixes deleting an eletion or vote throwing an error when uploading
  WabstiCExport files.
  [msom]

- Fixes sent notification prevents deleting votes and elections.
  [msom]

1.8.10 (2017-05-11)
~~~~~~~~~~~~~~~~~~~

- Fixes hovering over lakes throwing an error.
  [msom]

- Improves styling.
  [msom]

1.8.9 (2017-05-09)
~~~~~~~~~~~~~~~~~~~

- Adds sentry JavaScript error reporting support.
  [msom]

1.8.8 (2017-05-08)
~~~~~~~~~~~~~~~~~~~

- Adds mapdata for 2017.
  [msom]

1.8.7 (2017-05-04)
~~~~~~~~~~~~~~~~~~~

- Translates form errors when uploading WabstiCExport files.
  [msom]

- Adds tests.
  [msom]

1.8.6 (2017-05-02)
~~~~~~~~~~~~~~~~~~~

- Adds status/completed to elections and votes.
  [msom]

- Allows to specify the language when uploading WabstiCExport files.
  [msom]

- Parses the absolute majority when uploading WabstiCExport files.
  [msom]

- Parses the list connections when uploading WabstiCExport files.
  [msom]

- Evaluates the completed field of WabstiCExport files.
  [msom]

- Adds missing expats label in the election districts view of majorz elections.
  [msom]

- Visually groups elections and votes in the backend.
  [msom]

- Groups backend actions to dropdowns.
  [msom]

1.8.5 (2017-04-26)
~~~~~~~~~~~~~~~~~~~

- Fixes parsing an error field in WabstCiExport throwing an error.
  [msom]

1.8.4 (2017-04-25)
~~~~~~~~~~~~~~~~~~~

- Adds support for WabstCExport proporz elections.
  [msom]

1.8.3 (2017-04-24)
~~~~~~~~~~~~~~~~~~~

- Adds translations and visualization of expats.
  [msom]

1.8.2 (2017-04-24)
~~~~~~~~~~~~~~~~~~~

- Adds options for manual upload of WabstiCExport files.
  [msom]

- Tidies up usage of electoral districts somewhat.
  [msom]

- Fixes wrong default group when uploading majorz elections.
  [msom]

- Makes upload results views more robust.
  [msom]

1.8.1 (2017-04-21)
~~~~~~~~~~~~~~~~~~~

- Updates translations.
  [msom]

- Updates the static data.
  [msom]

- Fixes a division by zero error for invalid party results.
  [msom]

- Fixes the layout of majorz election factoids in the PDF.
  [msom]

1.8.0 (2017-04-18)
~~~~~~~~~~~~~~~~~~~

- Adds support for the wabsti exporter format.
  [msom]

- Fix providing giving an invalid archive date throwing an error.
  [msom]

- The type of vote (simple vs complex with counter proposal and tie-breaker)
  is set on the add/edit vote form instead of the upload form.
  [msom]

- Allows to upload the party results independently of the other results.
  [msom]

- Allows to set the absolute majority of majorz elections without uploading
  results.
  [msom]

- Use special, reserved numbers for expats.
  [msom]

- Fixes providing giving an invalid archive date throwing an error.
  [msom]

- Improves the performance of the send-sms command.
  [msom]

1.7.5 (2017-04-07)
~~~~~~~~~~~~~~~~~~~

- Shows the filename of the import errors.
  [msom]

- Renames the send sms command.
  [msom]

- Adds sentry option for fetch command.
  [msom]

- Hides empty sankey nodes.
  [msom]

- Fixes text ellipsis on sankey nodes.
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

- Fixes displaying the progress of complex votes.
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

- Adds elections and votes for municipalitites.

  **Breaking changes: The import and export formats have changed!
  Make sure to change your column names!**

  - Election: OneGov Cloud

    - election_counted_municipalities -> election_counted_entities
    - election_total_municipalities -> election_total_entities
    - municipality_name -> entity_name
    - municipality_bfs_number -> entity_bfs_number
    - municipality_elegible_voters -> entity_elegible_voters
    - municipality_received_ballots -> entity_received_ballots
    - municipality_blank_ballots -> entity_blank_ballots
    - municipality_invalid_ballots -> entity_invalid_ballots
    - municipality_unaccounted_ballots -> entity_unaccounted_ballots
    - municipality_accounted_ballots -> entity_accounted_ballots
    - municipality_blank_votes -> entity_blank_votes
    - municipality_invalid_votes -> entity_invalid_votes
    - municipality_accounted_votes -> entity_accounted_votes
    - municipality_bfs_number -> entity_id

  - Vote: OneGov Cloud

    - municipality_id -> entity_id

  - Vote: Default

    - BFS Nummer -> ID
    - Gemeinde -> Name

  [msom]

- Stores results of votes and elections in a separate table and allows
  to fetch results from other instances via command line interface.

  **Upgrading requires a manual extra step!**

  After running the upgrade, log in and visit *'update-results'*. This fixes
  the automatically generated URL linking to the elections and votes.

  [msom]

- Groups the elections and votes on the archive pages by date.
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
