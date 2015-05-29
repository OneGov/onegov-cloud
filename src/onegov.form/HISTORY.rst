Changelog
---------

Unreleased
~~~~~~~~~~

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
