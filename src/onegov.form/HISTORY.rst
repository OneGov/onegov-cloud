Changelog
---------

Unreleased
~~~~~~~~~~

0.5.2 (2015-06-09)
~~~~~~~~~~~~~~~~~~~

- Adds a 'received' field to the submissions which contains the time at which
  the submission was received.

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
