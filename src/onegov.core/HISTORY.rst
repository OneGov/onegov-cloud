Changelog
---------

Unreleased
~~~~~~~~~~

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
