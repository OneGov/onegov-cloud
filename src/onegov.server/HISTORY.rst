Changelog
---------

Unreleased
~~~~~~~~~~

0.1.0 (2015-10-12)
~~~~~~~~~~~~~~~~~~~

- Removes Python 2.x support.
  [href]

0.0.5 (2015-09-25)
~~~~~~~~~~~~~~~~~~~

- Stops accidentally messing with the encoding provided by the request.
  [href]

- Adds the ability to define the port for the onegov-server cli command.
  [href]

0.0.4 (2015-07-16)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to load yaml configs from string.
  [href]

- Remove support for Python 3.3.
  [href]

0.0.3 (2015-06-26)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to disable morepath autoconfig.
  [href]

- Pressing Ctrl+T in the onegov-server cli will now show a memory summary. This
  is helpful for determening if there are memory leaks or not.
  [href]

- Improves the debug server output, highlighting slow requests and dimming out
  redirects.
  [href]

- Include Morepath's upcoming changes to module imports until Morepath 0.11
  is released.
  [href]

0.0.2 (2015-04-30)
~~~~~~~~~~~~~~~~~~~

- Fixes onegov-server being unable to start when the packages are not stored
  as eggs.

  This fix might be unnnecessary in the future:
  https://github.com/morepath/morepath/issues/319

  [href]

0.0.1 (2015-04-29)
~~~~~~~~~~~~~~~~~~~

- Initial Release [href]
