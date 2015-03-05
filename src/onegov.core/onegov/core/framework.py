import hashlib
import inspect
import morepath
import os.path
import pylru

from cached_property import cached_property
from more.transaction import TransactionApp
from more.webassets import WebassetsApp
from more.webassets.core import webassets_injector_tween
from more.webassets.tweens import METHODS, CONTENT_TYPES
from onegov.core import cache
from onegov.core.orm import Base, SessionManager
from onegov.core.request import VirtualHostRequest
from onegov.server import Application as ServerApplication
from uuid import uuid4 as new_uuid


class Framework(TransactionApp, WebassetsApp, ServerApplication):
    """ Baseclass for Morepath OneGov applications. """

    request_class = VirtualHostRequest

    #: holds the database connection string, *if* there is a database connected
    dsn = None

    #: holdes the current schema associated with the database connection, set
    #: by and derived from :meth:`set_application_id`.
    schema = None

    @property
    def has_database_connection(self):
        """ onegov.core has good integration for Postgres using SQLAlchemy, but
        it doesn't require a connection.

        It's possible to have Onegov applications using a different database
        or not using one at all.

        """
        return self.dsn is not None

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

        :identity_secret_key:
            A random string used to sign the identity. By default a random
            string is generated. The drawback of this is the fact that
            users will be logged out every time the application restarts.

            So provide your own if you don't want that, but be sure to have
            a really long, really random key that you will never share
            with anyone!

        :memcached_url:
            The memcached url (default is 127.0.0.1:11211). If no memcached
            instance is found unning on that url, a dictionary is used
            for the cache instead.

        :memcached_connections:
            The maximum number of memcached connections that are available.
            Defaults to 100.

            This limit prevents a sophisticated attacker from starting a denial
            of service attack should he figure out a way to spawn lots of
            applications.

            Normally you want the combined memcached connection limit of all
            configured applications to be lower than the actual connection
            limit configured on memcached.

        """

        super(Framework, self).configure_application(**cfg)

        self.dsn = cfg.get('dsn')

        if self.dsn:
            self.session_manager = SessionManager(
                self.dsn, cfg.get('base', Base))

        self.identity_secure = cfg.get('identity_secure', True)
        self.identity_secret_key = cfg.get(
            'identity_secret_key', new_uuid().hex)

        self.memcached_url = cfg.get('memcached_url', '127.0.0.1:11211')
        self.memcached_connections = int(cfg.get('memcached_connections', 100))

        def on_cache_ejected(key, value):
            getattr(value, 'disconnect_all', lambda: None)()

        self._cache_backends = pylru.lrucache(
            self.memcached_connections, on_cache_ejected)

        self.cache_backend = 'dogpile.cache.pylibmc'
        self.cache_backend_arguments = {
            'url': self.memcached_url
        }

    def set_application_id(self, application_id):
        """ Set before the request is handled. Gets the schema from the
        application id and makes sure it exists, *if* a database connection
        is present.

        """
        super(Framework, self).set_application_id(application_id)
        self.schema = application_id.replace('/', '-')

        if self.has_database_connection:
            self.session_manager.set_current_schema(self.schema)

    @property
    def cache(self):
        """ Returns the cache backend for this application.

        The cache backend is a dogpile.cache backend. See:
        `<https://dogpilecache.readthedocs.org/>`_

        Once the `memcached_connections` limit defined in
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
