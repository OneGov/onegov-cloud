Changelog
---------
1.1.1 (2019-01-07)
~~~~~~~~~~~~~~~~~~~

- Fixes fetching events messing up the search index.
  [msom]

1.1.0 (2018-12-08)
~~~~~~~~~~~~~~~~~~~

- Allows to filter occurrences by locations.
  [msom]

1.0.0 (2018-12-07)
~~~~~~~~~~~~~~~~~~~

- Allows to filter occurrences by relative date ranges.
  [msom]

- Makes the ``outdated`` parameter of the occurrence collection stateful and
  more straightforward. If ``outdated`` is set to False, no outdated
  occurrences are returned no matter what start date is set.
  [msom]

- Fixes JSON import of recurring events.
  [msom]

- Fixes iCal export of events with indiviudal dates instead.
  [msom]

0.9.8 (2018-10-29)
~~~~~~~~~~~~~~~~~~~

- Optimizes fetch and guidle import.
  [msom]

0.9.7 (2018-10-19)
~~~~~~~~~~~~~~~~~~~

- Changes carriage return newlines to simple newlines.
  [href]

- Fixes ampersands in titles.
  [href]

- Gets the originals when downloading guidle images.
  [href]

0.9.6 (2018-10-19)
~~~~~~~~~~~~~~~~~~~

- Fixes importing events with images with no filename throwing an error.
  [msom]

0.9.5 (2018-10-18)
~~~~~~~~~~~~~~~~~~~

- Fixes files being imported with wrong content_type.
  [href]

0.9.4 (2018-10-18)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to link to external sources.
  [href]

- Sets the end-time of events ending at midnight a microsecond before 00:00.

  This is consistent with other parts of the application.
  [href]

0.9.3 (2018-10-17)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to associate a single image with each event.
  [href]

0.9.2 (2018-10-16)
~~~~~~~~~~~~~~~~~~~

- Fixes failing upgrade.
  [href]

0.9.1 (2018-10-16)
~~~~~~~~~~~~~~~~~~~

- Automatically turn complex rrules into rdate lists during import.
  [href]

- Strictly limits rrules to weekly rules and lists of rdates.
  [href]

0.9.0 (2018-09-24)
~~~~~~~~~~~~~~~~~~~

- Adds a source property to events.
  [msom]

0.8.1 (2018-09-24)
~~~~~~~~~~~~~~~~~~~

- Avoids indexing withdrawn events.
  [msom]

0.8.0 (2018-09-24)
~~~~~~~~~~~~~~~~~~~

- Adds a location parameter to the fetch command.
  [msom]

0.7.0 (2018-09-15)
~~~~~~~~~~~~~~~~~~~

- Adds ical export to occurrence collection.
  [msom]

- Adds tags, timestamp, uid and coordinates to ical exports.
  [msom]

- Adds ical import.
  [msom]

- Adds guidle import.
  [msom]

- Adds a command to fetch events from other instances.
  [msom]

- Makes the collections fully stateful.
  [msom]

- Fixes DST issue in occurrence generation.
  [msom]

- Fixes caluclation of the last occurrence of an event.
  [msom]

- Refactors the package.
  [msom]

- Removes unused code.
  [msom]

0.6.3 (2018-06-14)
~~~~~~~~~~~~~~~~~~~

- Stops indexing events before they are published.
  [href]

0.6.2 (2018-06-08)
~~~~~~~~~~~~~~~~~~~

- Adds a way to get the latest occurrence per event.
  [href]

0.6.1 (2017-12-29)
~~~~~~~~~~~~~~~~~~~

- Requires Python 3.6.
  [href]

- Moves the coordinates field to the model provided by onegov.gis.
  [href]

0.6.0 (2017-09-26)
~~~~~~~~~~~~~~~~~~~

- Switches to onegov.search's automatic language detection.
  [href]

0.5.1 (2016-09-23)
~~~~~~~~~~~~~~~~~~~

- Uses newly added onegov.core.utils.get_unique_hstore_keys function.
  [href]

0.5.0 (2016-08-18)
~~~~~~~~~~~~~~~~~~~

- Adds an organizer field.
  [href]

0.4.1 (2016-06-13)
~~~~~~~~~~~~~~~~~~~

- Exports events to iCalendar in UTC.
  [msom]

0.4.0 (2016-05-30)
~~~~~~~~~~~~~~~~~~~

- Removes cli commands.
  [msom]

- Fixes ical export test.
  [msom]

0.3.0 (2016-04-05)
~~~~~~~~~~~~~~~~~~~

- Adds onegov.gis coordinates to events.
  [href]

0.2.0 (2015-11-12)
~~~~~~~~~~~~~~~~~~~

- Adds CSV import and export.
  [msom]

0.1.0 (2015-10-12)
~~~~~~~~~~~~~~~~~~~

- Removes Python 2.x support.
  [href]

0.0.6 (2015-09-25)
~~~~~~~~~~~~~~~~~~~

- Adds onegov.search integration.
  [href]

0.0.5 (2015-09-15)
~~~~~~~~~~~~~~~~~~~

- Add an optional URL to ical exports.
  [msom]

- Cleanup the documentation.
  [msom]

0.0.4 (2015-09-08)
~~~~~~~~~~~~~~~~~~~

- Add cli command for guidle import (experimental).
  [msom]

- Add ical export functions.
  [msom]

0.0.3 (2015-09-03)
~~~~~~~~~~~~~~~~~~~

- Don't delete old event automatically.
  [msom]

0.0.2 (2015-08-28)
~~~~~~~~~~~~~~~~~~~

- Use hstore for tags.
  [msom]

- Filter for current occurrences by default.
  [msom]

- Add autoclean option to add event function.
  [msom]

- Add by_id method for event collections.
  [msom]

- Automatically remove old initiated events.
  [msom]

0.0.1 (2015-08-20)
~~~~~~~~~~~~~~~~~~~

- Initial Release
