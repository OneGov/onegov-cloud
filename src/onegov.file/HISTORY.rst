Changelog
---------

0.5.2 (2018-02-06)
~~~~~~~~~~~~~~~~~~~

- Excludes pdf/postscript files from the supported image formats.
  [href]

- Requires Python 3.6.
  [href]

0.5.1 (2017-12-22)
~~~~~~~~~~~~~~~~~~~

- Switches to onegov core's custom json module.
  [href]

0.5.0 (2017-11-14)
~~~~~~~~~~~~~~~~~~~

- Encodes X-File-Note results in json to avoid non-ASCII characters.
  [href]

0.4.0 (2017-09-22)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to link a bunch of files to any ORM model.
  [href]

0.3.2 (2017-01-26)
~~~~~~~~~~~~~~~~~~~

- Upgrades to the latest filedepot release, removing our hack.
  [href]

0.3.1 (2017-01-18)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to temporarily switch depot engines.
  [href]

0.3.0 (2017-01-03)
~~~~~~~~~~~~~~~~~~~

- Record the image dimensions when storing an image.
  [href]

0.2.3 (2016-09-28)
~~~~~~~~~~~~~~~~~~~

- Use onegov.core's svg sanitiser when adding an svg file.
  [href]

0.2.2 (2016-09-09)
~~~~~~~~~~~~~~~~~~~

- Supports latest filedepot release.
  [href]

0.2.1 (2016-08-19)
~~~~~~~~~~~~~~~~~~~

- Limits caching of HEAD request (alt-text) to one minute.
  [href]

0.2.0 (2016-07-27)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to update the file note through an AJAX call.
  [href]

- Adds HEAD request support for files.
  [href

- Return a custom X-File-Note header, when requesting an image. This header
  contains the value of the note field of the requested file.
  [href]

0.1.4 (2016-07-26)
~~~~~~~~~~~~~~~~~~~

- Orders files in relationships by last change date.
  [href]

0.1.3 (2016-07-20)
~~~~~~~~~~~~~~~~~~~

- Fixes polymorphic type attribute not working.
  [href]

0.1.2 (2016-07-20)
~~~~~~~~~~~~~~~~~~~

- Fixes query not filtering enough for typed collections.
  [href]

0.1.1 (2016-07-20)
~~~~~~~~~~~~~~~~~~~

- Fixes query not working correctly for typed collections.
  [href]

0.1.0 (2016-07-19)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to detect, find and prevent file duplicates.
  [href]

0.0.1 (2016-07-14)
~~~~~~~~~~~~~~~~~~~

- Initial Release
  [href]