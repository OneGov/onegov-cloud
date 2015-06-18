Changelog
---------

Unreleased
~~~~~~~~~~

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
