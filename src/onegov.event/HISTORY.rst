Changelog
---------
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
