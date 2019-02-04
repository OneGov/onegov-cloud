Changelog
---------

0.13.2 (2019-02-04)
~~~~~~~~~~~~~~~~~~~

- Removes dept files clean-up for assocations: Fixed upstream.
  [href]

0.13.1 (2019-01-18)
~~~~~~~~~~~~~~~~~~~

- Enables onegov.chat to use onegov.file and vice versa (circular import).
  [href]

- Fixes depot files not being cleaned when using associations.
  [href]

0.13.0 (2018-10-19)
~~~~~~~~~~~~~~~~~~~

- Increases the thumbnail and image sizes to properly support retina displays.
  [href]

0.12.2 (2018-10-11)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to locate signature metadata in the messages.
  [href]

0.12.1 (2018-10-11)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to query files by signature digest.
  [href]

- Fixes upgrades not working for older releases.
  [href]

- Adds a signature_timestamp hybrid-property.
  [href]

0.12.0 (2018-10-10)
~~~~~~~~~~~~~~~~~~~

- Migrates 'pages' to the more generic 'stats' dictionary which also
  includes a word count.
  [href]

- Adds log messages when signing a file and when removing a signed file.
  [href]

0.11.0 (2018-10-09)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to digitally sign PDF files.
  [href]

0.10.1 (2018-10-02)
~~~~~~~~~~~~~~~~~~~

- Fixes pdf extracts sometimes containing NUL characters.
  [href]

0.10.0 (2018-09-28)
~~~~~~~~~~~~~~~~~~~

- Extracts pdf text and page numbers for pdf uploads.
  [href]

- Adds the ability to implement searching on File subclasses.
  [href]

0.9.1 (2018-09-26)
~~~~~~~~~~~~~~~~~~~

- Fixes depot upgrade failing in certain cases.
  [href]

0.9.0 (2018-09-25)
~~~~~~~~~~~~~~~~~~~

- Fixes renames having no effect on the served response.
  [href]

- Fixes word documents being served with the wrong MIME-type.
  [href]

- Adds a 'signed' property to the file model.
  [href]

0.8.1 (2018-09-04)
~~~~~~~~~~~~~~~~~~~

- Fixes cache busting being overly eager.
  [href]

0.8.0 (2018-09-04)
~~~~~~~~~~~~~~~~~~~

- Adds a "published" state and a publication date to trigger it.
  [href]

- Changes frontend cache busting to use ORM events.
  [href]

0.7.0 (2018-08-06)
~~~~~~~~~~~~~~~~~~~

- Adds a cache busting hook to bust frontend caches when a file is deleted.
  [href]

- Adds PDF previews.
  [href]

0.6.1 (2018-06-21)
~~~~~~~~~~~~~~~~~~~

- Fixes upgrade.
  [href]

0.6.0 (2018-06-21)
~~~~~~~~~~~~~~~~~~~

- Adds a default order to the files.
  [href]

- Migrates the metadata storage to JSONB.
  [href]

- Improves query performance for selecting files in order.
  [href]

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