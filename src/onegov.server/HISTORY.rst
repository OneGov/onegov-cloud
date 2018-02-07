Changelog
---------

0.6.0 (2018-02-07)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to pass a generic exception handler to the server.
  [href]

0.5.0 (2018-01-31)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to override/extend wsgi environ contents.
  [href]

0.4.0 (2017-12-29)
~~~~~~~~~~~~~~~~~~~

- Requires Python 3.6.
  [href]

- Speeds up the first load slightly.
  [href]

- Adds the ability to pass '--pdb' to the onegov-server cli to enable
  post-mortem debugging.
  [href]

0.3.2 (2016-10-04)
~~~~~~~~~~~~~~~~~~~

- Fix application class not loading in Python 3.5.
  [href]

0.3.1 (2016-07-28)
~~~~~~~~~~~~~~~~~~~

- Support Morepath 0.15.
  [href]

- The development server no longer watches all subdirectories.

  It just watches the current directory (without recursion) and the src
  directory (with recursion). This makes the detection quite a bit faster at
  the cost of having to manually restart when something inside another folder
  changes (e.g in the parts/omelette folder).
  [href]

0.3.0 (2016-01-18)
~~~~~~~~~~~~~~~~~~~

- Replaces dashes with underscores in namespaces and application ids.

  This change ensures that combined application_ids can be used more readily
  to create database schemas (only the '/' needs to be replaced).

  It also makes it easier to route a subdomin directly to an application_id.
  Before there was a mismatch between the subdomain (with dashes) and the
  application_id (may or may not have dashes). Now the subdomain with dashes
  is transformed into an application_id without dashes - the new canonical
  form.

  [href]

0.2.0 (2016-01-14)
~~~~~~~~~~~~~~~~~~~

- Gives applications the abiilty to decide which application ids to handle.
  [href]

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
