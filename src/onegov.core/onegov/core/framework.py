""" The Framework provides a base Morepath application that offers certain
features for applications deriving from it:

 * Virtual hosting in conjunction with :mod:`onegov.server`.
 * Access to an SQLAlchemy session bound to a specific Postgres schema.
 * A cache backed by memcached, shared by multiple processes.
 * An identity policy with basic rules, permissions and role.
 * The ability to serve static files and css/js assets.

Using the framework does not really differ from using Morepath::

    from onegov.core.framework import Framework

    class MyApplication(Framework):
        pass

"""

import dectate
import hashlib
import inspect
import morepath
import pylru
import traceback
import random
import sys

from base64 import b64encode
from cached_property import cached_property
from datetime import datetime
from dectate import directive
from email.utils import parseaddr, formataddr
from itsdangerous import BadSignature, Signer
from mailthon.middleware import TLS, Auth
from morepath.publish import resolve_model, get_view_name
from more.content_security import ContentSecurityApp
from more.content_security import ContentSecurityPolicy
from more.content_security import SELF, UNSAFE_INLINE, UNSAFE_EVAL, NONE
from more.transaction import TransactionApp
from more.transaction.main import transaction_tween_factory
from more.webassets import WebassetsApp
from more.webassets.core import webassets_injector_tween
from more.webassets.tweens import METHODS, CONTENT_TYPES
from onegov.core import cache, log, utils
from onegov.core.custom import json
from onegov.core import directives
from onegov.core.cache import lru_cache
from onegov.core.datamanager import MailDataManager
from onegov.core.mail import email, Postman, MaildirPostman
from onegov.core.orm import Base, SessionManager, debug
from onegov.core.orm.cache import OrmCacheApp
from onegov.core.request import CoreRequest
from onegov.core.utils import PostThread
from onegov.server import Application as ServerApplication
from onegov.server.utils import load_class
from psycopg2.extensions import TransactionRollbackError
from purl import URL
from sqlalchemy.exc import OperationalError
from uuid import uuid4 as new_uuid
from urllib.parse import urlencode
from webob.exc import HTTPConflict


class Framework(
    TransactionApp,
    WebassetsApp,
    OrmCacheApp,
    ContentSecurityApp,
    ServerApplication
):
    """ Baseclass for Morepath OneGov applications. """

    request_class = CoreRequest

    #: holds the database connection string, *if* there is a database connected
    dsn = None

    #: holdes the current schema associated with the database connection, set
    #: by and derived from :meth:`set_application_id`.
    schema = None

    #: framework directives
    form = directive(directives.HtmlHandleFormAction)
    cronjob = directive(directives.CronjobAction)
    static_directory = directive(directives.StaticDirectoryAction)
    template_variables = directive(directives.TemplateVariablesAction)

    #: the request cache is initialised/emptied before each request
    request_cache = None

    @morepath.reify
    def __call__(self):
        """ Intercept all wsgi calls so we can attach debug tools. """

        fn = super().__call__
        fn = self.with_print_exceptions(fn)
        fn = self.with_request_cache(fn)

        if getattr(self, 'sql_query_report', False):
            fn = self.with_query_report(fn)

        if getattr(self, 'profile', False):
            fn = self.with_profiler(fn)

        return fn

    def with_query_report(self, fn):

        def with_query_report_wrapper(*args, **kwargs):
            with debug.analyze_sql_queries(self.sql_query_report):
                return fn(*args, **kwargs)

        return with_query_report_wrapper

    def with_profiler(self, fn):

        def with_profiler_wrapper(*args, **kwargs):
            filename = '{:%Y-%m-%d %H:%M:%S}.profile'.format(datetime.now())

            with utils.profile(filename):
                return fn(*args, **kwargs)

        return with_profiler_wrapper

    def with_request_cache(self, fn):

        def with_request_cache_wrapper(*args, **kwargs):
            self.clear_request_cache()
            return fn(*args, **kwargs)

        return with_request_cache_wrapper

    def with_print_exceptions(self, fn):

        def with_print_exceptions_wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception:
                if getattr(self, 'print_exceptions', False):
                    print("=" * 80, file=sys.stderr)
                    traceback.print_exc()
                raise

        return with_print_exceptions_wrapper

    def clear_request_cache(self):
        self.request_cache = {}

    @cached_property
    def modules(self):
        """ Provides access to modules used by the Framework class. Those
        modules cannot be included at the top because they themselves usually
        include the Framework.

        Admittelty a bit of a code smell.

        """
        from onegov.core import browser_session
        from onegov.core import cronjobs
        from onegov.core import filestorage
        from onegov.core import i18n
        from onegov.core import security
        from onegov.core import theme
        from onegov.core.security import rules

        return utils.Bunch(
            browser_session=browser_session,
            cronjobs=cronjobs,
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
        """ Configures the application. This function calls all methods on
        the current class which start with ``configure_``, passing the
        configuration as keyword arguments.

        The core itself supports the following parameters. Additional
        parameters are made available by extra ``configure_`` methods.

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

        :allow_shift_f5_comple:
            If true, the theme is recompiled if shift+f5 is done on the
            browser (or shift + reload button click).

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

        :mail:
            A dictionary keyed by e-mail category (i.e. 'marketing',
            'transactional') with the following subkeys:

                - host: The mail server to send e-mails from.
                - port: The port used for the mail server.
                - force_tls: True if TLS should be forced.
                - username: The mail username
                - password: The mail password
                - sender: The mail sender
                - use_directory: True if a mail directory should be used
                - directory: Path to the directory that should be used

        :mail_use_directory:
            If true, mails are stored in the maildir defined through
            ``mail_directory``. There, some other process is supposed to
            pick up the e-mails and send them.

        :mail_directory:
            The directory (maildir) where mails are stored if if
            ``mail_use_directory`` is set to True.

        :sql_query_report:
            Prints out a report sql queries for each request, unless False.
            Valid values are:

            * 'summary' (only show the number of queries)
            * 'redundant' (show summary and the actual redundant queries)
            * 'all' (show summary and all executed queries)

            Do not use in production!

        :profile:
            If true, profiles the request and stores the result in the profiles
            folder with the following format: ``YYYY-MM-DD hh:mm:ss.profile``

            Do not use in production!

        :print_exceptions:
            If true, exceptions are printed to stderr. Note that you should
            usually configure logging through onegov.server. This is mainly
            used for certain unit tests where we use WSGI more directly.

        """

        super().configure_application(**cfg)

        members = sorted(
            inspect.getmembers(self.__class__, callable),
            key=lambda item: item[0]
        )

        for n, method in members:
            if n.startswith('configure_') and n != 'configure_application':
                method(self, **cfg)

    def configure_dsn(self, **cfg):
        # certain namespaces are reserved for internal use:
        assert self.namespace not in {'global'}

        self.dsn = cfg.get('dsn')

        if self.dsn:
            self.session_manager = SessionManager(
                self.dsn, cfg.get('base', Base))

    def configure_memcached(self, **cfg):

        self.memcached_url = cfg.get('memcached_url', '127.0.0.1:11211')
        self.cache_connections = int(cfg.get('cache_connections', 100))

        def on_cache_ejected(key, value):
            getattr(value, 'disconnect_all', lambda: None)()

        self._caches = pylru.lrucache(self.cache_connections, on_cache_ejected)

        if cfg.get('disable_memcached', False):
            self.cache_backend = 'onegov.core.memory'
            self.cache_backend_arguments = {}
        else:
            self.cache_backend = 'onegov.core.memcached'
            self.cache_backend_arguments = {
                'url': self.memcached_url,
            }

    def configure_secrets(self, **cfg):

        self.identity_secure = cfg.get('identity_secure', True)

        # the identity secret is shared between tennants, so we name it
        # accordingly - use self.identity_secret to get a secret limited to
        # the current tennant
        self.unsafe_identity_secret = cfg.get(
            'identity_secret', new_uuid().hex)

        # same goes for the csrf_secret
        self.unsafe_csrf_secret = cfg.get('csrf_secret', new_uuid().hex)
        self.csrf_time_limit = int(cfg.get('csrf_time_limit', 1200))

        # you don't want these keys to be the same, see docstring above
        assert self.unsafe_identity_secret != self.unsafe_csrf_secret

        # you don't want to use the keys given in the example file
        assert self.unsafe_identity_secret != 'very-secret-key'

        # you don't want to use the keys given in the example file
        assert self.unsafe_csrf_secret != 'another-very-secret-key'

    def configure_yubikey(self, **cfg):
        self.yubikey_client_id = cfg.get('yubikey_client_id', None)
        self.yubikey_secret_key = cfg.get('yubikey_secret_key', None)

    def configure_filestorage(self, **cfg):

        if 'filestorage_object' in cfg:
            self._global_file_storage = cfg['filestorage_object']
            return

        if 'filestorage' in cfg:
            filestorage_class = load_class(cfg.get('filestorage'))
            filestorage_options = cfg.get('filestorage_options', {})

            # legacy support for pyfilesystem 1.x parameters
            if 'dir_mode' in filestorage_options:
                filestorage_options['create_mode'] \
                    = filestorage_options.pop('dir_mode')
        else:
            filestorage_class = None

        if filestorage_class:
            self._global_file_storage = filestorage_class(
                **filestorage_options)
        else:
            self._global_file_storage = None

    def configure_debug(self, **cfg):
        self.always_compile_theme = cfg.get('always_compile_theme', False)
        self.allow_shift_f5_compile = cfg.get('allow_shift_f5_compile', False)
        self.sql_query_report = cfg.get('sql_query_report', False)
        self.profile = cfg.get('profile', False)
        self.print_exceptions = cfg.get('print_exceptions', False)

    def configure_mail(self, **cfg):
        self.mail = cfg.get('mail', None)

        if self.mail:
            assert isinstance(self.mail, dict)
            assert 'transactional' in self.mail
            assert 'marketing' in self.mail

    def configure_hipchat(self, **cfg):
        self.hipchat_token = cfg.get('hipchat_token', None)
        self.hipchat_room_id = cfg.get('hipchat_room_id', None)

    def configure_zulip(self, **cfg):
        self.zulip_url = cfg.get('zulip_url', None)
        self.zulip_stream = cfg.get('zulip_stream', None)
        self.zulip_user = cfg.get('zulip_user', None)
        self.zulip_key = cfg.get('zulip_key', None)

    def configure_content_security_policy(self, **cfg):
        self.content_security_policy_enabled\
            = cfg.get('content_security_policy_enabled', True)

        self.content_security_policy_report_uri\
            = cfg.get('content_security_policy_report_uri', None)

        self.content_security_policy_report_only\
            = cfg.get('content_security_policy_report_only', False)

        self.content_security_policy_report_sample_rate\
            = cfg.get('content_security_policy_report_sample_rate', 0.001)

    def set_application_id(self, application_id):
        """ Set before the request is handled. Gets the schema from the
        application id and makes sure it exists, *if* a database connection
        is present.

        """
        super().set_application_id(application_id)

        # replace the dashes in the id with underlines since the schema
        # should not include double dashes and IDNA leads to those
        #
        # then, replace the '/' with a '-' so the only dash left will be
        # the dash between namespace and id
        self.schema = application_id.replace('-', '_').replace('/', '-')

        if self.has_database_connection:
            self.session_manager.set_current_schema(self.schema)

            if not self.is_orm_cache_setup:
                self.setup_orm_cache()

    def get_cache(self, namespace, expiration_time=None, backend=None,
                  backend_args=None):
        """ Creates a new cache backend for this application or reuses an
        existing one. Each backend is bound to a namespace and has its own
        expiration time (ttl).

        Once the `cache_connections` limit defined in
        :meth:`configure_application` is reached, the backends are removed,
        with the least recently used one being discarded first.

        """

        if namespace not in self._caches:
            backend = backend or self.cache_backend
            backend_args = backend_args or self.cache_backend_arguments

            if backend == 'dogpile.cache.memory':
                expiration_time = backend_args = None

            self._caches[namespace] = cache.create_backend(
                namespace=namespace,
                expiration_time=expiration_time,
                backend=backend,
                arguments=backend_args,
            )

        return self._caches[namespace]

    @property
    def session_cache(self):
        """ A cache that is kept for as long as possible. """
        return self.get_cache(self.application_id + ':s')

    @property
    def cache(self):
        """ A cache that might be invalidated frequently. """
        return self.get_cache(self.application_id + ':x', expiration_time=3600)

    @property
    def settings(self):
        return self.config.setting_registry

    @property
    def application_id_hash(self):
        """ The application_id as hash, use this if the applicaiton_id can
        be read by the user -> this obfuscates things slightly.

        """
        # sha-1 should be enough, because even if somebody was able to get
        # the cleartext value I honestly couldn't tell you what it could be
        # used for...
        return hashlib.sha1(self.application_id.encode('utf-8')).hexdigest()

    def object_by_path(self, path, with_view_name=False):
        """ Takes a path and returns the object associated with it. If a
        scheme or a host is passed it is ignored.

        Be careful if you use this function with user provided urls, we load
        objects here, not views. Therefore no security restrictions apply.

        The first use case of this function is to provide a generic copy/paste
        functionality. There, we only allow urls to be copied which have been
        previously signed by the server.

        *Safeguards like this are necessary if the user has the ability to
        somehow influence the path*!

        """

        # strip host and scheme
        path = URL(path).path()

        request = self.request_class(environ={
            'PATH_INFO': URL(path).path(),
            'SERVER_NAME': '',
            'SERVER_PORT': '',
            'SERVER_PROTOCOL': 'https'
        }, app=self)

        obj = resolve_model(request)

        # if there is more than one token unconsumed, this can't be a view
        if len(request.unconsumed) > 1:
            return (None, None) if with_view_name else None

        if with_view_name:
            return obj, get_view_name(request.unconsumed) or None

        return obj

    def permission_by_view(self, model, view_name=None):
        """ Returns the permission required for the given model and view_name.

        The model may be an instance or a class.

        If the view cannot be evaluated, a KeyError is raised.

        """
        assert model is not None

        model = model if inspect.isclass(model) else model.__class__
        predicates = {'name': view_name} if view_name else {}

        query = dectate.Query('view')
        query = query.filter(model=model, predicates=predicates)

        try:
            action, handler = next(query(self.__class__))
        except (StopIteration, RuntimeError):
            raise KeyError(
                "{!r} has no view named {}".format(model, view_name))

        return action.permission

    @cached_property
    def session(self):
        """ Alias for self.session_manager.session. """
        return self.session_manager.session

    @lru_cache(maxsize=2)
    def postman(self, category):
        """ Returns a Mailthon postman configured with the mail settings in
        the settings view. See `<http://mailthon.readthedocs.org/>`_ for
        more information.

        """
        config = self.mail[category]

        if config['use_directory']:
            assert config['directory']

            return MaildirPostman(
                host=None,
                port=None,
                options=dict(maildir=config['directory'])
            )
        else:
            assert config['host']
            assert config['port']

            middlewares = []

            if config['force_tls']:
                middlewares.append(TLS(force=True))

            if config['username']:
                middlewares.append(
                    Auth(
                        username=config['username'],
                        password=config['password']
                    )
                )

            return Postman(
                host=config['host'],
                port=config['port'],
                middlewares=middlewares
            )

    def send_marketing_email(self, *args, **kwargs):
        """ Sends an e-mail categorised as marketing. This includes but is not
        limited to:

            * Announcements
            * Newsletters
            * Promotional E-Mails

        When in doubt, send a marketing e-mail. Transactional e-mails are
        sacred and should only be used if necessary. This ensures that the
        important stuff is reaching our customers!

        """
        kwargs['category'] = 'marketing'
        return self.send_email(*args, **kwargs)

    def send_transactional_email(self, *args, **kwargs):
        """ Sends an e-mail categorised as transactional. This is limited to:

            * Welcome emails
            * Reset passwords emails
            * Notifications
            * Weekly digests
            * Receipts and invoices

        """
        kwargs['category'] = 'transactional'
        return self.send_email(*args, **kwargs)

    def send_email(self, reply_to, category='marketing',
                   receivers=(), cc=(), bcc=(), subject=None, content=None,
                   encoding='utf-8', attachments=(), headers={}):
        """ Sends a plain-text e-mail using :attr:`postman` to the given
        recipients. A reply to address is used to enable people to answer
        to the e-mail which is usually sent by a noreply kind of e-mail
        address.

        E-mails sent through this method are bound to the current transaction.
        If that transaction is aborted or not commited, the e-mail is not sent.

        Usually you'll use this method inside a request, where transactions
        are automatically commited at the end.

        For more complex use cases have a look at
        `<http://mailthon.readthedocs.org/>`_.

        """
        assert category in ('transactional', 'marketing')

        sender = self.mail[category]['sender']
        assert sender

        # if the reply to address has a name part (Name <address@host>), use
        # the name part for the sender address as well to somewhat hide the
        # fact that we're using a noreply email
        name, address = parseaddr(reply_to)

        if name and not parseaddr(sender)[0]:
            sender = formataddr((name, sender))

        envelope = email(
            sender=sender,
            receivers=receivers,
            cc=cc,
            bcc=bcc,
            subject=subject,
            content=content,
            encoding=encoding,
            attachments=attachments,
            category=category
        )

        envelope.headers['Sender'] = sender
        envelope.headers['Reply-To'] = formataddr((name, address))

        for key, value in headers.items():
            envelope.headers[key] = value

        # send e-mails through the transaction machinery
        MailDataManager.send_email(self.postman(category), envelope)

    def send_hipchat(self, message_from, message, message_format='html',
                     color='green', notify=True):
        """ Sends a hipchat message asynchronously.

        We are using the room notification method of the hipchat API V2:
        `<https://www.hipchat.com/docs/apiv2/method/send_room_notification/>`_

        Make sure to generate a token for the room (Scope: Send Notifications)
        and define it in the configuration.

        Returns the thread object to allow waiting by calling join.

        """

        if self.hipchat_token and self.hipchat_room_id:
            data = json.dumps({
                'from': message_from,
                'message': message,
                'message_format': message_format,
                'color': color,
                'notify': notify
            }).encode('utf-8')

            headers = (
                ('Authorization', 'Bearer {}'.format(self.hipchat_token)),
                ('Content-Type', 'application/json; charset=utf-8'),
                ('Content-Length', len(data)),
            )

            url = 'https://api.hipchat.com/v2/room/{}/notification'.format(
                self.hipchat_room_id
            )

            thread = PostThread(url, data, headers)
            thread.start()

            return thread

    def send_zulip(self, subject, content):
        """ Sends a hipchat message asynchronously.

        We are using the stream message method of zulip:
        `<https://zulipchat.com/api/stream-message>`_

        Returns the thread object to allow waiting by calling join.

        """

        if all((
            self.zulip_url, self.zulip_stream, self.zulip_user, self.zulip_key
        )):
            data = urlencode({
                'type': 'stream',
                'to': self.zulip_stream,
                'subject': subject,
                'content': content
            }).encode('utf-8')

            auth = b64encode(
                '{}:{}'.format(self.zulip_user, self.zulip_key).encode('ascii')
            )
            headers = (
                ('Authorization', 'Basic {}'.format(auth.decode("ascii"))),
                ('Content-Type', 'application/x-www-form-urlencoded'),
                ('Content-Length', len(data)),
            )

            thread = PostThread(self.zulip_url, data, headers)
            thread.start()

            return thread

    @cached_property
    def static_files(self):
        """ A list of static_files paths registered through the
        :class:`onegov.core.directive.StaticDirectoryAction` directive.

        To register a static files path::

            @App.static_directory()
            def get_static_directory():
                return 'static'

        For this to work, ``server_static_files`` has to be set to true.

        When a child application registers a directory, the directory will
        be considered first, before falling back to the parent's static
        directory.

        """
        return getattr(self.config.staticdirectory_registry, 'paths', [])[::-1]

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
        return morepath.authentication.Identity(
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
            app.filestorage.settext(filename, 'Lorem Ipsum')

            # returns either an url like '/files/4ec56cc005c594880a...'
            # or maybe 'https://amazonaws.com/onegov-cloud/32746/220592/q...'
            request.filestorage_link(filename)

        """
        if self._global_file_storage is None:
            return None

        return utils.makeopendir(self._global_file_storage, self.schema)

    @property
    def themestorage(self):
        """ Returns a storage object meant for themes, shared by all
        applications.

        Only use this for theming, nothing else!

        """

        if self._global_file_storage is None:
            return None

        return utils.makeopendir(self._global_file_storage, 'global-theme')

    @property
    def theme_options(self):
        """ Returns the application-bound theme options. """
        return {}

    @cached_property
    def translations(self):
        """ Returns all available translations keyed by langauge. """

        try:
            if not self.settings.i18n.localedirs:
                return {}

            return self.modules.i18n.get_translations(
                self.settings.i18n.localedirs
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
    def locales(self):
        """ Returns all available locales in a set. """
        try:
            if self.settings.i18n.locales:
                return self.settings.i18n.locales
        except AttributeError:
            pass

        return set(self.translations.keys())

    @property
    def identity_secret(self):
        """ The identity secret, guaranteed to only be valid for the current
        application id.

        """

        return self.unsafe_identity_secret + self.application_id_hash

    @property
    def csrf_secret(self):
        """ The identity secret, guaranteed to only be valid for the current
        application id.

        """

        return self.unsafe_csrf_secret + self.application_id_hash

    def sign(self, text):
        """ Signs a text with the identity secret.

        The text is signed together with the application id, so if one
        application signs a text another won't be able to unsign it.

        """
        signer = Signer(self.identity_secret, salt='generic-signer')
        return signer.sign(text.encode('utf-8')).decode('utf-8')

    def unsign(self, text):
        """ Unsigns a signed text, returning None if unsuccessful. """
        try:
            signer = Signer(self.identity_secret, salt='generic-signer')
            return signer.unsign(text).decode('utf-8')
        except BadSignature:
            return None


@Framework.webasset_url()
def get_webasset_url():
    """ The webassets url needs to be unique so we can fix it before
        returning the generated html. See :func:`fix_webassets_url_factory`.

    """
    return '7da9c72a3b5f9e060b898ef7cd714b8a'  # do *not* change this hash!


@Framework.webasset_filter('js')
def get_js_filter():
    return 'rjsmin'


@Framework.webasset_filter('css')
def get_css_filter():
    return 'custom-rcssmin'


@Framework.webasset_filter('jsx', produces='js')
def get_jsx_filter():
    return 'jsx'


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

        original_url = '/' + request.app.config.webasset_registry.url
        adjusted_url = request.transform(request.script_name + original_url)

        response.body = response.body.replace(
            original_url.encode('utf-8'),
            adjusted_url.encode('utf-8')
        )

        return response

    return fix_webassets_url


@Framework.setting(section='transaction', name='attempts')
def get_retry_attempts():
    return 2


@Framework.setting(section='cronjobs', name='enabled')
def get_cronjobs_enabled():
    """ If this value is set to False, all cronjobs are disabled. Only use
    this during testing. Cronjobs have no impact on your application, unless
    there are defined cronjobs, in which case they are there for a reason.

    """
    return True


@Framework.setting(section='content_security_policy', name='default')
def default_content_security_policy():
    """ The default content security policy used throughout OneGov. """

    return ContentSecurityPolicy(
        # by default limit to self
        default_src={SELF},

        # allow fonts from practically anywhere (no mixed content though)
        font_src={SELF, "http:", "https:", "data:"},

        # allow images from practically anywhere (no mixed content though)
        img_src={SELF, "http:", "https:", "data:"},

        # enable inline styles and external stylesheets
        style_src={SELF, "https:", UNSAFE_INLINE},

        # enable inline scripts, eval and external scripts
        script_src={SELF, "https:", UNSAFE_INLINE, UNSAFE_EVAL},

        # do not enable any object/embed/applet elements
        object_src={NONE},

        # disable all mixed content (https -> http)
        block_all_mixed_content=True
    )


@Framework.setting(section='content_security_policy', name='apply_policy')
def default_policy_apply_factory():
    """ Adds the content security policy report settings from the yaml. """

    def apply_policy(policy, request, response):
        if not request.app.content_security_policy_enabled:
            return

        sample_rate = request.app.content_security_policy_report_sample_rate
        report_only = request.app.content_security_policy_report_only

        if random.uniform(0, 1) <= sample_rate:
            report_uri = request.app.content_security_policy_report_uri
        else:
            report_uri = None

        policy.report_uri = report_uri or ''
        policy.report_only = report_only

        policy.apply(response)

    return apply_policy


@Framework.tween_factory(over=transaction_tween_factory)
def http_conflict_tween_factory(app, handler):
    def http_conflict_tween(request):
        """ When two transactions conflict, postgres raises an error which
        more.transaction handles by retrying the transaction for the configured
        amount of time. See :func:`get_retry_attempts`.

        Once it exhausts all retries, it reraises the exception. Since that
        doesn't give the user any information, we turn this general error into
        a 409 Conflict code so we can show a custom error page on the server.

        """

        try:
            return handler(request)
        except OperationalError as e:
            if not hasattr(e, 'orig'):
                raise

            if not isinstance(e.orig, TransactionRollbackError):
                raise

            log.warning("A transaction failed because there was a conflict")

            return HTTPConflict()

    return http_conflict_tween


@Framework.tween_factory(under=http_conflict_tween_factory)
def current_language_tween_factory(app, handler):
    def current_language_tween(request):
        """ Set the current language on the session manager for each request,
        for translatable database columns.

        """

        if app.has_database_connection:
            app.session_manager.set_locale(
                default_locale=request.default_locale,
                current_locale=request.locale
            )

        return handler(request)

    return current_language_tween


@Framework.tween_factory(under=current_language_tween_factory)
def spawn_cronjob_thread_tween_factory(app, handler):

    from onegov.core.cronjobs import ApplicationBoundCronjobs
    registry = app.config.cronjob_registry

    if not hasattr(registry, 'cronjobs'):
        return handler

    if not app.settings.cronjobs.enabled:
        return handler

    assert app.has_database_connection, """
        Cronjobs require a database connection for inter-process locking.
    """

    def spawn_cronjob_thread_tween(request):
        if app.application_id not in registry.cronjob_threads:
            thread = ApplicationBoundCronjobs(
                request, registry.cronjobs.values(), app.session_manager
            )

            registry.cronjob_threads[request.app.application_id] = thread

            thread.start()

        return handler(request)

    return spawn_cronjob_thread_tween
