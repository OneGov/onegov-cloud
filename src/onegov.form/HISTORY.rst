Changelog
---------
0.16.2 (2016-12-28)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to supply a custom field_id to the formbuilder.
  [href]

0.16.1 (2016-12-23)
~~~~~~~~~~~~~~~~~~~

- HTML escapes labels in the dynamic formbuilder for security.
  [href]

0.16.0 (2016-12-06)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to define ensure_* functions on forms which get called
  automatically by the validate function.
  [href]

0.15.2 (2016-10-10)
~~~~~~~~~~~~~~~~~~~

- Adds a process_obj function which may be overridden by forms that need
  to change the way objects are processed.
  [href]

0.15.1 (2016-10-06)
~~~~~~~~~~~~~~~~~~~

- Make sure that empty fieldsets are cleaned up when a field is deleted.
  [href]

0.15.0 (2016-09-23)
~~~~~~~~~~~~~~~~~~~

- Adds an ordered multi checkbox field.
  [href]

0.14.0 (2016-09-09)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to move in a form class.
  [href]

0.13.0 (2016-08-30)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to delete fields from forms/all fieldsets.
  [href]

0.12.1 (2016-07-06)
~~~~~~~~~~~~~~~~~~~

- Adds compatibility with python-magic 0.4.12.
  [msom]

0.12.0 (2016-06-10)
~~~~~~~~~~~~~~~~~~~

- Adds new options on how to dependen on a field value.

  It's now possible to depend on NOT a specific field value and to depend on
  more then one fields (AND).
  [msom]

0.11.2 (2016-05-11)
~~~~~~~~~~~~~~~~~~~

- Exclude pyparsing 2.1.2 from the list of possible versions.

  It doesn't work together with python 3.3 and 3.4.
  [href]

0.11.1 (2016-04-14)
~~~~~~~~~~~~~~~~~~~

- Ignores depends_on argument to fields if it is set to None.
  [href]

0.11.0 (2016-04-13)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to block reserved field names with the validator.
  [href]

- Adds the ability to exclude certain fields from the submission update.
  [href]

0.10.2 (2016-04-11)
~~~~~~~~~~~~~~~~~~~

- Stops escaping strings in the submission title (that's the frontends job).
  [href]

0.10.1 (2016-04-01)
~~~~~~~~~~~~~~~~~~~

- Properly include lead/text as properties.

  They were basically there already and other code counted on this being so.
  [href]

0.10.0 (2016-03-24)
~~~~~~~~~~~~~~~~~~~

- Improves wtform's populate_obj by adding include and exclude filters to it.
  [href]

- Moves map related code (like the coordinates field) to onegov.gis.
  [href]

- Adds the ability to merge multiple forms together while keeping the field
  order predictable.
  [href]

0.9.0 (2016-03-23)
~~~~~~~~~~~~~~~~~~~

- Makes it simpler to add a dependent field through Python code.
  [href]

- Adds a field representing coordinates (lat/lon).
  [href]

0.8.6 (2016-03-17)
~~~~~~~~~~~~~~~~~~~

- Fixes unexpected indentation detection not working correctly.
  [href]

0.8.5 (2016-02-02)
~~~~~~~~~~~~~~~~~~~

- Marks fields which contain labels as such, so the field rendering code can
  avoid generating nested labels.

0.8.4 (2016-01-28)
~~~~~~~~~~~~~~~~~~~

- Uses the latest onegov.core release to get rid of some code.
  [href]

0.8.3 (2015-11-26)
~~~~~~~~~~~~~~~~~~~

- Adds an error message if no actual field was defined in a definition.
  [href]

0.8.2 (2015-11-18)
~~~~~~~~~~~~~~~~~~~

- Adds an error message if the form indentation is wrong.
  [href]

- Adds an error message for duplicate labels.
  [href]

- Fixes fieldsets only showing up once on static forms.
  [href]

0.8.1 (2015-10-15)
~~~~~~~~~~~~~~~~~~~

- Use 'de_CH' translation instead of 'de'
  [href]

0.8.0 (2015-10-12)
~~~~~~~~~~~~~~~~~~~

- Removes Python 2.x support.
  [href]

0.7.3 (2015-10-08)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to force the UploadWidget to show no special options.
  [href]


0.7.2 (2015-10-05)
~~~~~~~~~~~~~~~~~~~

- Adds German translations, no more defining those outside the package.
  [href]

0.7.1 (2015-09-25)
~~~~~~~~~~~~~~~~~~~

- Adds onegov.search integration for form definitions.
  [href]

0.7.0 (2015-09-10)
~~~~~~~~~~~~~~~~~~~

- Fixes an error where optional fields had to be filled out.
  [href]

- Adds rudimentary syntax checking with information about which line wrong.
  [href]

0.6.9 (2015-08-28)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to specifiy the submission id manually.
  [href]

- Adds the ability to pass a custom base class to the parse_form function.
  [href]

0.6.8 (2015-08-26)
~~~~~~~~~~~~~~~~~~~

- Adds an easier way for the often used "check if there's a required e-mail".
  [href]

- Adds the ability to add submissions whose form definitions are external.
  [href]

0.6.7 (2015-08-18)
~~~~~~~~~~~~~~~~~~~

- Adds a new widget for multiple checkbox fields.
  [href]

0.6.6 (2015-08-11)
~~~~~~~~~~~~~~~~~~~

- Fixes installation issue with pip.
  [href]

0.6.5 (2015-07-13)
~~~~~~~~~~~~~~~~~~~

- Fix expired submission removal not working if files had been uploaded.
  [href]

0.6.4 (2015-07-09)
~~~~~~~~~~~~~~~~~~~

- The default form definition validator now checks that there's at least one
  required E-Mail field.

0.6.3 (2015-07-02)
~~~~~~~~~~~~~~~~~~~

- Adds a method to get all useful data from a form.
  [href]

- Use content/meta defined in onegov.core.
  [href]

0.6.2 (2015-06-26)
~~~~~~~~~~~~~~~~~~~

- Remove accidentally left in upgrade test code.
  [href]

0.6.1 (2015-06-26)
~~~~~~~~~~~~~~~~~~~

- Adds support for onegov.core.upgrade.
  [href]

- Remove support for Python 3.3.
  [href]

0.6.0 (2015-06-10)
~~~~~~~~~~~~~~~~~~~

- Compress files using gzip instead of zlib, as the former is better supported.
  [href]

- Change the submission complete method, ensuring the right polymorphic
  instance is returned afterwards.
  [href]

- Make sure the received date is only set once.
  [href]

0.5.4 (2015-06-10)
~~~~~~~~~~~~~~~~~~~

- Adds a helpful ``has_submissions`` function on the form definition model.
  [href]

- Automatically delete pending submissions when removing a definition.
  [href]

0.5.3 (2015-06-10)
~~~~~~~~~~~~~~~~~~~

- Adds a function to retrieve form definitions together with the number of
  complete submissions.
  [href]

0.5.2 (2015-06-09)
~~~~~~~~~~~~~~~~~~~

- Adds a 'received' field to the submissions which contains the time at which
  the submission was received.
  [href]

- Adds an email and a title field to the submission.
  [href]

- Adds the ability to scope a submission collection to a specific form.
  [href]

0.5.1 (2015-06-08)
~~~~~~~~~~~~~~~~~~~

- Store all information, even invalid one, to avoid accidentally throwing
  away error information.
  [href]

- Fixes time field triggering an error.
  [href]

0.5.0 (2015-06-05)
~~~~~~~~~~~~~~~~~~~

- Adds a *very* simple form syntax parser.
  [href]

- Fixes password field not working.
  [href]

- Uses the right class for form-definitions depending on the type.
  [href]

0.4.1 (2015-06-03)
~~~~~~~~~~~~~~~~~~~

- Stores a checksum with each form definition and submission.
  [href]

- Adds the ability to filter out submissions older than one hour.
  [href]

0.4.0 (2015-06-03)
~~~~~~~~~~~~~~~~~~~

- Moves the uploaded files to their own table.
  [href]

0.3.1 (2015-06-02)
~~~~~~~~~~~~~~~~~~~

- Fixes unicode error in Python 2.7.
  [href]

0.3.0 (2015-06-02)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to render fields for html output (without input elements).
  [href]

- Adds the ability to upload files without losing them if the form has an
  unrelated validation error.
  [href]

- Divides the submissions into 'pending' and 'complete'.

  Pending submissions are temporary and possibly invalid. Complete submissions
  are final and always valid.

  [href]

- Compresses uploaded files before storing them on the database.
  [href]

- Limits the size of uploaded files.
  [href]

- No longer stores the csrf_token with the form submission.
  [href]

- Adds a file upload syntax.
  [href]

- Show the 'required' flag, even if the requirement is conditional.
  [href]

0.2.3 (2015-05-29)
~~~~~~~~~~~~~~~~~~~

- Fix unicode errors in Python 2.7.
  [href]

0.2.2 (2015-05-29)
~~~~~~~~~~~~~~~~~~~

- Make sure special fields like the csrf token are included in the fieldsets.
  [href]

0.2.1 (2015-05-28)
~~~~~~~~~~~~~~~~~~~

- Makes sure multiple fields with the same labels are handled more
  intelligently.
  [href]

0.2.0 (2015-05-28)
~~~~~~~~~~~~~~~~~~~

- Rewrites most of the parsing logic. Pyparsing is no longer used for
  indentation, instead the form source is transalted into YAML first, then
  parsed further.

  This fixes all known indentation problems.

  [href]

0.1.0 (2015-05-22)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to store forms and related submissions in the database.
  [href]

- Adds a custom markdownish form syntax.

  See http://onegov.readthedocs.org/en/latest/onegov_form.html#module-onegov.form.parser.grammar
  [href]

0.0.1 (2015-04-29)
~~~~~~~~~~~~~~~~~~~

- Initial Release [href]
