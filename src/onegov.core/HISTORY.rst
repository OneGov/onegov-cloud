Changelog
---------
0.30.1 (2016-10-17)
~~~~~~~~~~~~~~~~~~~

- Improves the performance of the unique hstore keys utility function.
  [href]

- Improves the performance of pagination collections by speeding up the count.
  [href]

0.30.0 (2016-10-11)
~~~~~~~~~~~~~~~~~~~

- Adds a convenient and safe way to define return-to url parameters.
  [href]

- Fixes request.url not having the same semantics as webob.request.url.
  [href]

- Adds the ability to query form class associated with a model.
  [href]

0.29.3 (2016-10-07)
~~~~~~~~~~~~~~~~~~~

- Gets SQLAlchemy-Utils' aggregates decorator to work with the session manager.
  [href]

0.29.2 (2016-10-06)
~~~~~~~~~~~~~~~~~~~

- Forms handled through the form directive may now define a `on_request`
  method, which is called after the request has been bound to the form and
  before the view is handled.
  [href]

- Adds an utility function to remove repeated spaces.
  [href]

0.29.1 (2016-10-04)
~~~~~~~~~~~~~~~~~~~

- Adds compatibility with Morepath 0.16.
  [href]

0.29.0 (2016-10-04)
~~~~~~~~~~~~~~~~~~~

- Introduces a generic collection meant to share common functionalty.
  [href]

0.28.0 (2016-09-28)
~~~~~~~~~~~~~~~~~~~

- Moves the html sanitizer to its own module and introduce an svg sanitizer.
  [href]

0.27.2 (2016-09-26)
~~~~~~~~~~~~~~~~~~~

- Fixes get_unique_hstore_keys failing if the hstore is set to None.
  [href]

0.27.1 (2016-09-23)
~~~~~~~~~~~~~~~~~~~

- Adds an utility function to fetch unique hstore keys from a table.
  [href]

0.27.0 (2016-09-21)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to override a specific macro in child applications.
  [href]

- Supports a wider range of objects which may be cached. Uses 'dill' to
  accomplish this.
  [href]

- Removes the runtime bound cache again as it's not that useful.
  [href]

0.26.0 (2016-09-09)
~~~~~~~~~~~~~~~~~~~

- Adds a runtime bound cache, not shared between processes and able to
  accept any kind of object to cache (no pickling).
  [href]

0.25.1 (2016-09-01)
~~~~~~~~~~~~~~~~~~~

- Adds a uuid morepath converter.
  [href]

- Fixes variable directive resulting in overwrites instead of merges.
  [href]

0.25.0 (2016-08-26)
~~~~~~~~~~~~~~~~~~~

- Introduces a member role, which is close to an anonymous user in terms
  of access, but allows to differentiate between ananymous and registered
  users.
  [href]

0.24.0 (2016-08-24)
~~~~~~~~~~~~~~~~~~~

- Adds a template variable directive, which gives applications the ability
  to inject their own global variables into templates.
  [href]

- Fixes formatting date failing if the date is None.
  [msom]

0.23.0 (2016-08-23)
~~~~~~~~~~~~~~~~~~~

- Adds a static directory directive, which gives applications the ability
  to define their own static directory and for inherited applications to
  append a path to the list of static directory paths.
  [href]

- Moves two often used helpers to the base layout.
  [href]

- Adds a HTML5 (RFC3339) date converter for Morepath.
  [href]

0.22.1 (2016-07-28)
~~~~~~~~~~~~~~~~~~~

- Adds compatibility with Morepath 0.15.
  [href]

0.22.0 (2016-07-14)
~~~~~~~~~~~~~~~~~~~

- Adds an utility function to search for orm models.
  [href]

- Explicitly prohibit unsynchronized bulk updates with a helpful assertion.
  [href]

- Exports the random token length constant.
  [href]

0.21.3 (2016-07-06)
~~~~~~~~~~~~~~~~~~~

- Adds compatibility with python-magic 0.4.12.
  [msom]

0.21.2 (2016-06-06)
~~~~~~~~~~~~~~~~~~~

- Disable debug output when running cli commands.
  [href]

- Adds the ability to manually define the csv dialect.
  [href]

- Adds the ability to access csv files without any known headers.
  [href]

0.21.1 (2016-05-31)
~~~~~~~~~~~~~~~~~~~

- No longer print the selector when running a command.
  [href]

- Use a single connection during cli commands.
  [href]

- Adds the ability to configure the connection pool of the session manager.
  [href]

- Stops cronjobs from being activated during cli commands.
  [href]

0.21.0 (2016-05-30)
~~~~~~~~~~~~~~~~~~~

- Introduces a simpler way to write cli commands.
  [href]

0.20.2 (2016-05-13)
~~~~~~~~~~~~~~~~~~~

- Adds support for transforming lists if *irregular* dicts to csv and xlsx.
  [href]

0.20.1 (2016-04-29)
~~~~~~~~~~~~~~~~~~~

- Removes escaping characters from plaintext e-mails.
  [href]

0.20.0 (2016-04-11)
~~~~~~~~~~~~~~~~~~~

- Switch to new more.webassets release.
  [href]

0.19.0 (2016-04-06)
~~~~~~~~~~~~~~~~~~~

- Adds Morepath 0.13 compatibility.
  [href]

0.18.2 (2016-04-05)
~~~~~~~~~~~~~~~~~~~

- Fixes meta/content failing if the dictionary is None.
  [href]

0.18.1 (2016-04-01)
~~~~~~~~~~~~~~~~~~~

- Adds a custom datauri filter to work aorund an issue with webassets.
  [href]

0.18.0 (2016-03-24)
~~~~~~~~~~~~~~~~~~~

- Adds helper methods for accessing meta/content dicts through properties.
  [href]

0.17.2 (2016-02-15)
~~~~~~~~~~~~~~~~~~~

- Improves CSV handling.
  [msom]

- Ensures that the sendmail limit is an integer.
  [href]

0.17.1 (2016-02-11)
~~~~~~~~~~~~~~~~~~~

- Fixes certain form translations being stuck on the first request's locale.
  [href]

0.17.0 (2016-02-08)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to limit the number of emails to be processed in one go.
  [href]

- Allows to optionally pick the sheet when converting excel files to CSV.
  [msom]

0.16.1 (2016-02-02)
~~~~~~~~~~~~~~~~~~~

- Fixes connection pool exhaustion occuring when upgrading many tennants.
  [href]

0.16.0 (2016-01-28)
~~~~~~~~~~~~~~~~~~~

- Adds a method to lookup the polymorphic class of any polymorphic identity.
  [href]

0.15.2 (2016-01-27)
~~~~~~~~~~~~~~~~~~~

- Fixes wrong exception being caught for undelivarable e-mails.
  [href]

0.15.1 (2016-01-26)
~~~~~~~~~~~~~~~~~~~

- Removes undeliverable e-mails from the maildir queue.
  [href]

0.15.0 (2016-01-20)
~~~~~~~~~~~~~~~~~~~

- Exclude dots from normalized urls.
  [href]

0.14.0 (2016-01-20)
~~~~~~~~~~~~~~~~~~~

- Caches the result of po file compiles.
  [href]

0.13.4 (2016-01-18)
~~~~~~~~~~~~~~~~~~~

- Slightly improves normalize_for_url for German.
  [href]

0.13.3 (2016-01-18)
~~~~~~~~~~~~~~~~~~~

- Stops the form directive from chocking up if no form is returned.
  [href]

0.13.2 (2016-01-07)
~~~~~~~~~~~~~~~~~~~

- Stops cronjobs sometimes running twice in one minute.
  [href]

0.13.1 (2016-01-05)
~~~~~~~~~~~~~~~~~~~

- Fixes cronjobs not working with more than one process.
  [href]

0.13.0 (2015-12-31)
~~~~~~~~~~~~~~~~~~~

- Adds a cronjob directive to specify tasks which have to run at an exact time.
  [href]

- Adds a distributed lock mechanism using postgres.
  [href]

0.12.3 (2015-12-21)
~~~~~~~~~~~~~~~~~~~

- Fixes incorrect year in date format. Before the week's year was used instead
  of the date's year. This lead to incorrect output when formatting a date.
  [href]

0.12.2 (2015-12-18)
~~~~~~~~~~~~~~~~~~~

- Ensures a proper cleanup of the existing db schemas before completeing the
  transfer command.
  [href]

0.12.1 (2015-12-17)
~~~~~~~~~~~~~~~~~~~

- Fixes broken dependency.
  [href]

0.12.0 (2015-12-16)
~~~~~~~~~~~~~~~~~~~

- Includes a plain text alternative in all HTML E-Mails.
  [href]

0.11.2 (2015-12-15)
~~~~~~~~~~~~~~~~~~~

- Fixes cache expiration time having no effect.
  [href]

0.11.1 (2015-12-15)
~~~~~~~~~~~~~~~~~~~

- Fixes site locale creating many instead of one locale cookie.
  [href]

0.11.0 (2015-12-15)
~~~~~~~~~~~~~~~~~~~

- Adds a site locale model and renames 'languages' to 'locales'.
  [href]

0.10.0 (2015-12-14)
~~~~~~~~~~~~~~~~~~~

- Integrates localized database fields.

  Use ``onegov.core.orm.translation_hybrid`` together with sqlalchemy utils:
  http://sqlalchemy-utils.readthedocs.org/en/latest/internationalization.html

- Shares the session_manager with all ORM mapped instances which may access
  it through ``self.session_manager``.

  This is a plumbing feature to enable integration of localized database
  fields.
  [href]

- Adds a method to automatically scan all morepath dependencies. It is not
  guaranteed to always work and should only be relied upon for testing and
  upgrades.
  [href]

0.9.0 (2015-12-10)
~~~~~~~~~~~~~~~~~~~

- Adds a method which takes a list of dicts and turns it into a csv string.
  [href]

- Adds a method which takes a list of dicts and turns it into a xlsx.
  [href]

0.8.1 (2015-12-08)
~~~~~~~~~~~~~~~~~~~

- Attaches the current request to each form instance, allowing for
  validation logic on the form which talks to the database.
  [href]

0.8.0 (2015-11-20)
~~~~~~~~~~~~~~~~~~~

- Adds a random password generator (for pronouncable passwords).
  [href]

- Adds yubikey_client_id and yubikey_secret_key to configuration.
  [href]

0.7.5 (2015-10-26)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to convert xls/xlsx files to csv.
  [href]

- Fixes empty lines in csv tripping up the parser in unexpected ways.
  [href]

0.7.4 (2015-10-21)
~~~~~~~~~~~~~~~~~~~

- Adjacency lists are now always ordered by the value in their 'order' column.

  When adding new items to a parent, A-Z is enforced between the children, as
  long as the children are already sorted A-Z. Once this holds no longer true,
  no sorting will be imposed on the unsorted children until they are sorted
  again.
  [href]

- Adds missing space to long date formats.
  [href]

0.7.3 (2015-10-15)
~~~~~~~~~~~~~~~~~~~

- Fix being unable to load languages not conforming to our exact format.
  [href]

0.7.2 (2015-10-15)
~~~~~~~~~~~~~~~~~~~

- Improves i18n support, removing bugs, adding support for de_CH and the like.
  [href]

- The format_number function now uses the locale specific grouping/decimal
  separators.
  [href]

0.7.1 (2015-10-13)
~~~~~~~~~~~~~~~~~~~

- The csv encoding detection function will now either look for cp1152 or utf-8.
  [href]

0.7.0 (2015-10-12)
~~~~~~~~~~~~~~~~~~~

- Drops Python 2 support!
  [href]

- Adds a csv module which helps with importing flawed csv files.
  [href]

0.6.2 (2015-10-07)
~~~~~~~~~~~~~~~~~~~

- Adds an is_subpath function.
  [href]

0.6.1 (2015-10-05)
~~~~~~~~~~~~~~~~~~~

- Adds a relative_url utility function.
  [href]

- Merges multiple translations into one for faster lookups.
  [href]

0.6.0 (2015-10-02)
~~~~~~~~~~~~~~~~~~~

- Allows more than one translation directory to be set by the application. This
  enables us to use translations defined in packages outside the app. For
  example, onegov.form now keeps its own translations. Onegov.town and
  onegov.election_day simply point to onegov.form's translations to have
  them included.
  [href]

0.5.1 (2015-09-11)
~~~~~~~~~~~~~~~~~~~

- Adds an utility function to check if an object is iterable but not a string.
  [href]

0.5.0 (2015-09-10)
~~~~~~~~~~~~~~~~~~~

- E-Mails containing unicode are now sent properly.
  [href]

- Adds on_insert/on_update/on_delete signals to the session manager.
  [href]

0.4.28 (2015-09-07)
~~~~~~~~~~~~~~~~~~~

- Adds a is_uuid utility function.
  [href]

- Limits the 'subset' call for Pagination collections to once per instance.
  [href]

0.4.27 (2015-08-31)
~~~~~~~~~~~~~~~~~~~

- Fixes ``has_column`` upgrade function not checking the given table.
  [href]

- Fixes browser session chocking on an invalid cookie.
  [href]

0.4.26 (2015-08-28)
~~~~~~~~~~~~~~~~~~~

- Fixes more than one task per module crashing the upgrade.
  [href]

- Always run upgrades may now indicate if they did anything useful. If not,
  they are hidden from the upgrade output.
  [href]

0.4.25 (2015-08-24)
~~~~~~~~~~~~~~~~~~~

- The upgrades table is now prefilled with all modules and tasks, when the
  schema is first created. Fixes #8.
  [href]

- Ensures unique upgrade task function names. See #8.
  [href]

0.4.24 (2015-08-20)
~~~~~~~~~~~~~~~~~~~

- Adds support page titles consisting solely on emojis.
  [href]

- Transactions are now automatically retried once if they fail. If the second
  attempt also fails, a 409 Conflict HTTP Code is returned.
  [href]

0.4.23 (2015-08-14)
~~~~~~~~~~~~~~~~~~~

- Binds all e-mails to the transaction. Only if the transaction commits are
  the e-mails sent.

- The memcached key is now limited in its size.
  [href]

- Properly support postgres extensions.
  [href]

0.4.22 (2015-08-12)
~~~~~~~~~~~~~~~~~~~

- Fixes more unicode email sending issues.
  [href]

0.4.21 (2015-08-12)
~~~~~~~~~~~~~~~~~~~

- Adds a helper function that puts a scheme in front of urls without one.
  [href]

0.4.20 (2015-08-12)
~~~~~~~~~~~~~~~~~~~

- Linkify now escapes all html by default (except for the 'a' tag).
  [href]

- Adds proper support for unicode email addresses (only the domain and the
  text - the local part won't be supported for now as it is rare and doesn't
  even pass Chrome's or Firefox's email validation).
  [href]

- Removes the default order_by clause on adjacency lists.
  [href]

- Adds the ability to profile requests and selected pieces of code.
  [href]

0.4.19 (2015-08-10)
~~~~~~~~~~~~~~~~~~~

- Use bcrypt instead of py-bcrypt as the latter has been deprecated by passlib.
  [href]

- Support hstore types.
  [msom]

0.4.18 (2015-08-06)
~~~~~~~~~~~~~~~~~~~

- Adds a function that returns the object associated with a path.
  [href]

- Fix options not being translated on i18n-enabled forms.
  [href]

0.4.17 (2015-08-04)
~~~~~~~~~~~~~~~~~~~

- Replaces pylibmc with python-memcached, with the latter now having Python 3
  support.
  [href]

- Fix onegov-core upgrade hanging forever.
  [href]

0.4.16 (2015-07-30)
~~~~~~~~~~~~~~~~~~~

- Make sure we don't get a circulare dependency between the connection and
  the session.
  [href]

- Adds the ability to define multiple bases on the session manager.
  [href]

- Switch postgres isolation level to SERIALIZABLE for all sessions.
  [href]

0.4.15 (2015-07-29)
~~~~~~~~~~~~~~~~~~~

- Gets rid of global state used by the session manager.
  [href]

- Adds the ability to define configurations in independent methods (allowing
  for onegov.core.Framework extensions to provide their own configuration).
  [href]

- Adds functions to create and deserialize URL safe tokens.
  [msom]

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
