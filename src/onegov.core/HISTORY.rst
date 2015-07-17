Changelog
---------

Unreleased
~~~~~~~~~~

0.4.14 (2015-07-17)
~~~~~~~~~~~~~~~~~~~

- Adds a sendmail command that replaces repoze.sendmail's qp.
  [href]

0.4.13 (2015-07-16)
~~~~~~~~~~~~~~~~~~~

- Adds a data transfer command to download data from a onegov cloud server and
  install them locally. Requires ssh permissions to function.

- Adds the ability to send e-mails to a maildir, instead of directly to an
  SMTP server.
  [href]

0.4.12 (2015-07-15)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to render a template directly.
  [href]

0.4.11 (2015-07-14)
~~~~~~~~~~~~~~~~~~~

- Make sure upgrade steps are only added once per record.
  [href]

- Add ``has_column`` function to upgrade context.
  [href]

0.4.10 (2015-07-14)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to render a single chameleon macro.
  [href]

0.4.9 (2015-07-13)
~~~~~~~~~~~~~~~~~~~

- Adds a relative date function to the layout.
  [href]

0.4.8 (2015-07-13)
~~~~~~~~~~~~~~~~~~~

- Adds a pagination base class for use with collections.
  [href]

- Adds an isodate format function to the layout base.
  [href]

0.4.7 (2015-07-08)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to send emails.
  [href]

0.4.6 (2015-07-06)
~~~~~~~~~~~~~~~~~~~

- Pass the request in addition to the model when dynamically building the
  form class in the form directive.
  [href]

- Fixes onegov.core.utils.rchop not working correctly.
  [href]

0.4.5 (2015-07-02)
~~~~~~~~~~~~~~~~~~~

- Fixes SQLAlchemy error occurring if more than one model used the new 
  AdjacencyList base class.
  [href]

0.4.4 (2015-07-01)
~~~~~~~~~~~~~~~~~~~

- Adds a content mixin for meta/content JSON fields.
  [href]

- Adds an abstract AdjacencyList implementation (refactored from onegov.page).
  [href]

- Adds quote_plus and unquote_plus to compat imports.
  [treinhard]

0.4.3 (2015-06-30)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to format numbers through the layout class.
  [href]

0.4.2 (2015-06-29)
~~~~~~~~~~~~~~~~~~~

- Added a new 'hidden_from_public' property which may be set on any model
  handled by onegov.core Applications. If said property is found and it is
  True, anonymous users are forbidden from viewing it.

  This enables applications to dynamically set the visibilty of any model.
  [href]

0.4.1 (2015-06-26)
~~~~~~~~~~~~~~~~~~~

- Ensure that the bind schema doesn't stick around to cause test failures.
  [href]

0.4.0 (2015-06-26)
~~~~~~~~~~~~~~~~~~~

- Removes support for Python 3.3. Use 2.7 or 3.3.
  [href]

- Adds colors to the sql debug output.
  [href]

- Fix json encoder/decode not working with lists and generators.
  [href]

0.3.9 (2015-06-23)
~~~~~~~~~~~~~~~~~~~

- Moves sanitize_html and linkify functions from onegov.town to core.
  [href]

0.3.8 (2015-06-18)
~~~~~~~~~~~~~~~~~~~

- Remove parentheses from url when normalizing it.
  [href]

0.3.7 (2015-06-17)
~~~~~~~~~~~~~~~~~~~

- Adds a groupby function that returns lists instead of generators.
  [href]

- Include a layout base class useful for applications that render html.
  [href]

- Stop throwing an error if no translation is registered.
  [href]

0.3.6 (2015-06-12)
~~~~~~~~~~~~~~~~~~~

- Fix encoding error when generating the theme on certain platforms.
  [href]

- Make sure the last_change timestamp property works for single objects.
  [href]

0.3.5 (2015-06-03)
~~~~~~~~~~~~~~~~~~~

- Adds a convenience property to timestamps that returns either the modified-
  or the created-timestamp.
  [href]

0.3.4 (2015-06-03)
~~~~~~~~~~~~~~~~~~~

- Fixes SQL statement debugger failing if a statement is executed with a list
  of parameters.
  [href]

0.3.3 (2015-06-02)
~~~~~~~~~~~~~~~~~~~

- Accepts wtform's data attribute in request.get_form.
  [href]

0.3.2 (2015-05-29)
~~~~~~~~~~~~~~~~~~~

- Fix pofile loading not working in certain environments.
  [href]

0.3.1 (2015-05-28)
~~~~~~~~~~~~~~~~~~~

- Adds a method to list all schemas found in the database.
  [href]

0.3.0 (2015-05-20)
~~~~~~~~~~~~~~~~~~~

- Introduces a custom json encoder/decoder that handles additional types.
  [href]

0.2.0 (2015-05-18)
~~~~~~~~~~~~~~~~~~~

- Tighten security around static file serving.
  [href]

- Urls generated from titles no longer contain double dashes ('--').
  [href]

- The browser session now only adds a session_id to the cookies if there's
  a change in the browser session.
  [href]

- Adds the ability to count and print the sql queries that go into a single
  request.
  [href]

- Store all login information server-side. The client only gets a random
  session id scoped to the application.
  [href]

- Make sure that signatures are only valid for the origin application.
  [href]

0.1.0 (2015-05-06)
~~~~~~~~~~~~~~~~~~~

- The form directive now also accepts a factory function.
  [href]

0.0.2 (2015-05-05)
~~~~~~~~~~~~~~~~~~~

- The CSRF protection now associates a random secret with the session. The
  random secret is then used to check if the CSRF token is valid.
  [href]

- Cache the translator on the request to be slightly more efficient.
  [href]

0.0.1 (2015-04-29)
~~~~~~~~~~~~~~~~~~~

- Initial Release [href]
