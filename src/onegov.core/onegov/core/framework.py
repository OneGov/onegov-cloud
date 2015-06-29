""" The Framework provides a base Morepath application that offers certain
features for applications deriving from it:

 * Virtual hosting in conjunction with :mod:`onegov.server`.
 * Access to an SQLAlchemy session bound to a specific Postgres schema.
 * A cache backed by memcached, shared by multiple processes.
 * An identity policy with basic rules, permissions and role.
 * The ability to serve static files and css/js assets.

Using the framework does not really differ from using Morepath::

    from onegov.core import Framework

    class MyApplication(Framework):
        pass

"""

import hashlib
import inspect
import morepath
import os.path
import pydoc
import pylru

from cached_property import cached_property
from itsdangerous import BadSignature, Signer
from more.transaction import TransactionApp
from more.webassets import WebassetsApp
from more.webassets.core import webassets_injector_tween
from more.webassets.tweens import METHODS, CONTENT_TYPES
from onegov.core import cache
from onegov.core import utils
from onegov.core.orm import Base, SessionManager, debug
from onegov.core.request import CoreRequest
from onegov.server import Application as ServerApplication
from uuid import uuid4 as new_uuid


class Framework(TransactionApp, WebassetsApp, ServerApplication):
    """ Baseclass for Morepath OneGov applications. """

    request_class = CoreRequest

    #: holds the database connection string, *if* there is a database connected
    dsn = None

    #: holdes the current schema associated with the database connection, set
    #: by and derived from :meth:`set_application_id`.
    schema = None

    def __call__(self, environ, start_response):
        """ Intercept all wsgi calls so we can attach debug tools. """

        if getattr(self, 'sql_query_report', False) is False:
            return super(Framework, self).__call__(environ, start_response)

        with debug.analyze_sql_queries(self.sql_query_report):
            return super(Framework, self).__call__(environ, start_response)

    @cached_property
    def modules(self):
        """ Provides access to modules used by the Framework class. Those
        modules cannot be included at the top because they themselves usually
        include the Framework.

        Admittelty a bit of a code smell.

        """
        from onegov.core import browser_session
        from onegov.core import filestorage
        from onegov.core import i18n
        from onegov.core import security
        from onegov.core import theme
        from onegov.core.security import rules

        return utils.Bunch(
            browser_session=browser_session,
            filestorage=filestorage,
            i18n=i18n,
            security=security,
            rules=rules,
            theme=theme
        )

    @property
    def has_database_connection(self):
        """ onegov.core has good integration for Postgres using SQLAlchemy, but
        it doesn't require a connection.

        It's possible to have Onegov applications using a different database
        or not using one at all.

        """
        return self.dsn is not None

    @property
    def has_filestorage(self):
        """ Returns true if :attr:`fs` is available. """
        return self._global_file_storage is not None

    def configure_application(self, **cfg):
        """ Configures the application, supporting the following parameters:

        :dsn:
            The database connection to use. May be None.

            See :meth:`onegov.core.orm.session_manager.setup`

        :base:
            The declarative base class used. By default,
            :attr:`onegov.core.orm.Base` is used.

        :identity_secure:
            True if the identity cookie is only transmitted over https. Only
            set this to False during development!

        :identity_secret:
            A random string used to sign the identity. By default a random
            string is generated. The drawback of this is the fact that
            users will be logged out every time the application restarts.

            So provide your own if you don't want that, but be sure to have
            a really long, really random key that you will never share
            with anyone!

        :memcached_url:
            The memcached url (default is 127.0.0.1:11211). If memcached
            isn't running the cache will not be used, though the memcached
            server can be started at any time at which point the application
            will connect to it again.

        :cache_connections:
            The maximum number of connections to the cache that are available.
            Defaults to 100. This is mostly relevant for memcached, though
            it works for all kinds of caches.

            This limit prevents a sophisticated attacker from starting a denial
            of service attack should he figure out a way to spawn lots of
            applications.

            Normally you want the combined memcached connection limit of all
            configured applications to be lower than the actual connection
            limit configured on memcached.

        :disable_memcached:
            If True, memcache will not be used. The cache will be entirely in
            the memory of the current process (so no sharing between multiple
            processes).

        :file_storage:
            The file_storage module to use. See
            `<http://docs.pyfilesystem.org/en/latest/filesystems.html>`_

        :file_storage_options:
            A dictionary of options passed to the ``__init__`` method of the
            file_storage class.

            The file storage is expected to work as is. For example, if
            ``fs.osfs.OSFS`` is used, the root_path is expected exist.

            The file storage can be shared between different onegov.core
            applications. Each application automatically gets its own
            namespace inside this space.

        :always_compile_theme:
            If true, the theme is always compiled - no caching is employed.

        :csrf_secret:
            A random string used to sign the csrf token. Make sure this differs
            from ``identity_secret``! The algorithms behind identity_secret and
            the csrf protection differ. If the same secret is used we might
            leak information about said secret.

            By default a random string is generated. The drawback of this is
            the fact that users won't be able to submit their forms if the
            app is restarted in the background.

            So provide your own, but be sure to have a really long, really
            random string that you will never share with anyone!

        :csrf_time_limit:
            The csrf time limit in seconds. Basically the amount of time a
            user has to submit a form, from the time it's rendered.

            Defaults to 1'200s (20 minutes).

        :sql_query_report:
            Prints out a report sql queries for each request, unless False.
            Valid values are:

            * 'summary' (only show the number of queries)
            * 'redundant' (show summary and the actual redundant queries)
            * 'all' (show summary and all executed queries)

            Do not use in production!

        """

        super(Framework, self).configure_application(**cfg)

        # certain namespaces are reserved for internal use:
        assert self.namespace not in {'global'}

        self.dsn = cfg.get('dsn')

        if self.dsn:
            self.session_manager = SessionManager(
                self.dsn, cfg.get('base', Base))

        self.identity_secure = cfg.get('identity_secure', True)
        self.identity_secret = cfg.get('identity_secret', new_uuid().hex)

        self.memcached_url = cfg.get('memcached_url', '127.0.0.1:11211')
        self.cache_connections = int(cfg.get('cache_connections', 100))

        def on_cache_ejected(key, value):
            getattr(value, 'disconnect_all', lambda: None)()

        self._cache_backends = pylru.lrucache(
            self.cache_connections, on_cache_ejected)

        if cfg.get('disable_memcached', False):
            self.cache_backend = 'dogpile.cache.memory'
            self.cache_backend_arguments = {}
        else:
            self.cache_backend = 'dogpile.cache.pylibmc'
            self.cache_backend_arguments = {
                'url': self.memcached_url
            }

        self.csrf_secret = cfg.get('csrf_secret', new_uuid().hex)
        self.csrf_time_limit = int(cfg.get('csrf_time_limit', 1200))

        # you don't want these keys to be the same, see docstring above
        assert self.identity_secret != self.csrf_secret

        # you don't want to use the keys given in the example file
        assert self.identity_secret != 'very-secret-key'

        # you don't want to use the keys given in the example file
        assert self.csrf_secret != 'another-very-secret-key'

        if 'filestorage' in cfg:
            filestorage_class = pydoc.locate(cfg.get('filestorage'))
            filestorage_options = cfg.get('filestorage_options', {})
        else:
            filestorage_class = None

        if filestorage_class:
            self._global_file_storage = filestorage_class(
                **filestorage_options)
        else:
            self._global_file_storage = None

        self.always_compile_theme = cfg.get('always_compile_theme', False)
        self.sql_query_report = cfg.get('sql_query_report', False)

    def set_application_id(self, application_id):
        """ Set before the request is handled. Gets the schema from the
        application id and makes sure it exists, *if* a database connection
        is present.

        """
        super(Framework, self).set_application_id(application_id)

        # replace the dashes in the id with underlines since the schema
        # should not include double dashes and IDNA leads to those
        #
        # then, replace the '/' with a '-' so the only dash left will be
        # the dash between namespace and id
        self.schema = application_id.replace('-', '_').replace('/', '-')
        if self.has_database_connection:
            self.session_manager.set_current_schema(self.schema)

    @property
    def cache(self):
        """ Returns the cache backend for this application.

        The cache backend is a dogpile.cache backend. See:
        `<https://dogpilecache.readthedocs.org/>`_

        Once the `cache_connections` limit defined in
        :meth:`configure_application` is reached, the backends are removed,
        with the least recently used one being discarded first.

        """
        if self.application_id not in self._cache_backends:
            self._cache_backends[self.application_id] = cache.create_backend(
                namespace=self.application_id,
                backend=self.cache_backend,
                arguments=self.cache_backend_arguments,
                expiration_time=None)

        return self._cache_backends[self.application_id]

    @property
    def application_id_hash(self):
        """ The application_id as hash, use this if the applicaiton_id can
        be read by the user -> this obfuscates things slightly.

        """
        # sha-1 should be enough, because even if somebody was able to get
        # the cleartext value I honestly couldn't tell you what it could be
        # used for...
        return hashlib.sha1(self.application_id.encode('utf-8')).hexdigest()

    @cached_property
    def webassets_url(self):
        """ The webassets url needs to be unique so we can fix it before
        returning the generated html. See :func:`fix_webassets_url_factory`.

        """

        return '7da9c72a3b5f9e060b898ef7cd714b8a'  # do *not* change this hash!

    @cached_property
    def session(self):
        """ Alias for self.session_manager.session. """
        return self.session_manager.session

    @cached_property
    def static_files(self):
        """ Absolute path to the static files. Defaults to the folder
        of the application + ``/static``.

        """
        app_path = os.path.dirname(inspect.getfile(self.__class__))
        return os.path.join(app_path, 'static')

    @cached_property
    def serve_static_files(self):
        """ Returns True if ``/static`` files should be served. Needs to be
        enabled manually.

        Note that even if the static files are not served, ``/static`` path
        is still served, it just won't return anything but a 404.

        Note also that static files are served **publicly**. You can override
        this in your application, but doing that and testing for it is on you!

        See also: :mod:`onegov.core.static`. """
        return False

    def application_bound_identity(self, userid, role):
        """ Returns a new morepath identity for the given userid and role,
        bound to this application.

        """
        return morepath.security.Identity(
            userid, role=role, application_id=self.application_id_hash)

    @property
    def filestorage(self):
        """ Returns a filestorage object bound to the current application.
        Based on this nifty module:

        `<http://docs.pyfilesystem.org/en/latest/>`_

        The file storage returned is guaranteed to be independent of other
        applications (the scope is the application_id, not just the class).

        There is no guarantee as to what file storage backend is actually used.
        It's quite possible that the file storage will be somewhere online
        in the future (e.g. S3).

        Therefore, the urls for the file storage should always be acquired
        through :meth:`onegov.core.request.CoreRequest.filestorage_link`.

        The backend is configured through :meth:`configure_application`.

        For a list of methods available on the resulting object, consult this
        list: `<http://docs.pyfilesystem.org/en/latest/interface.html>`_.

        If no filestorage is available, this returns None.
        See :attr:`self.has_filestorage`.

        WARNING: Files stored in the filestorage are available publicly! All
        someone has to do is to *guess* the filename. To get an unguessable
        filename use :meth:`onegov.core.filestorage.random_filename`.

        The reason for this is the fact that filestorage may be something
        external in the future.

        This should not deter you from using this for user uploads, though
        you should be careful. If you want to be sure that your application
        stores files locally, use some other ways of storing those files.

        Example::

            from onegov.core import filestorage

            filename = filestorage.random_filename()
            app.filestorage.setcontents(filename, 'Lorem Ipsum')

            # returns either an url like '/files/4ec56cc005c594880a...'
            # or maybe 'https://amazonaws.com/onegov-cloud/32746/220592/q...'
            request.filestorage_link(filename)

        """
        if self._global_file_storage is None:
            return None

        return self._global_file_storage.makeopendir(self.schema)

    @property
    def themestorage(self):
        """ Returns a storage object meant for themes, shared by all
        applications.

        Only use this for theming, nothing else!

        """

        if self._global_file_storage is None:
            return None

        return self._global_file_storage.makeopendir('global-theme')

    @property
    def theme_options(self):
        """ Returns the application-bound theme options. """
        return {}

    @cached_property
    def translations(self):
        """ Returns all available translations keyed by langauge. """

        try:
            if not self.registry.settings.i18n.domain:
                return {}

            if not self.registry.settings.i18n.localedir:
                return {}

            return self.modules.i18n.get_translations(
                self.registry.settings.i18n.domain,
                self.registry.settings.i18n.localedir
            )
        except AttributeError:
            return {}

    @cached_property
    def chameleon_translations(self):
        """ Returns all available translations for chameleon. """
        return self.modules.i18n.wrap_translations_for_chameleon(
            self.translations
        )

    @cached_property
    def languages(self):
        """ Returns all available languages in a set. """
        return set(self.translations.keys())

    def sign(self, text):
        """ Signs a text with the identity secret.

        The text is signed together with the application id, so if one
        application signs a text another won't be able to unsign it.

        """
        signer = Signer(self.identity_secret, salt=self.application_id)
        return signer.sign(text.encode('utf-8')).decode('utf-8')

    def unsign(self, text):
        """ Unsigns a signed text, returning None if unsuccessful. """
        try:
            signer = Signer(self.identity_secret, salt=self.application_id)
            return signer.unsign(text).decode('utf-8')
        except BadSignature:
            return None


@Framework.tween_factory(over=webassets_injector_tween)
def fix_webassets_url_factory(app, handler):
    def fix_webassets_url(request):
        """ more.webassets is not aware of our virtual hosting situation
        introduced by onegov.server - therefore it doesn't produce the right
        urls. This is something Morepath would have to fix.

        This is why we fix the html here, after it has been created, changing
        the url to the fixed version. We do this by examining the unique
        assets url.

        This means that someone could theoretically have something replaced
        that is not meant to be replaced, but that would be incredibly
        unlikely.

        If someone intentionally does we would at best have some broken urls
        on the site.

        """
        response = handler(request)

        if not response.content_type:
            return response

        if request.method not in METHODS:
            return response

        if response.content_type.lower() not in CONTENT_TYPES:
            return response

        original_url = '/' + request.app.webassets_url
        adjusted_url = request.transform(request.script_name + original_url)

        response.body = response.body.replace(
            original_url.encode('utf-8'),
            adjusted_url.encode('utf-8')
        )

        return response

    return fix_webassets_url
