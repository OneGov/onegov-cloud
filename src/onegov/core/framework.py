""" The Framework provides a base Morepath application that offers certain
features for applications deriving from it:

 * Virtual hosting in conjunction with :mod:`onegov.server`.
 * Access to an SQLAlchemy session bound to a specific Postgres schema.
 * A cache backed by redis, shared by multiple processes.
 * An identity policy with basic rules, permissions and role.
 * The ability to serve static files and css/js assets.

Using the framework does not really differ from using Morepath::

    from onegov.core.framework import Framework

    class MyApplication(Framework):
        pass

"""
from __future__ import annotations

import dectate
import hashlib
import inspect
import io
import json
import morepath
import os.path
import random
import sys
import traceback

from base64 import b64encode
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from datetime import datetime
from dectate import directive
from functools import cached_property, wraps
from itsdangerous import BadSignature, Signer
from libres.db.models import ORMBase
from morepath import dispatch_method
from morepath.publish import resolve_model, get_view_name
from more.content_security import ContentSecurityApp
from more.content_security import ContentSecurityPolicy
from more.content_security import NONE, SELF, UNSAFE_INLINE
from more.transaction import TransactionApp
from more.transaction.main import transaction_tween_factory
from more.webassets import WebassetsApp
from more.webassets.core import webassets_injector_tween
from more.webassets.tweens import METHODS, CONTENT_TYPES
from reg import ClassIndex

from onegov.core import cache, log, utils
from onegov.core import directives
from onegov.core.crypto import stored_random_token
from onegov.core.datamanager import FileDataManager
from onegov.core.mail import prepare_email
from onegov.core.orm import (
    Base, SessionManager, debug, DB_CONNECTION_ERRORS)
from onegov.core.orm.cache import OrmCacheApp
from onegov.core.orm.observer import ScopedPropertyObserver
from onegov.core.request import CoreRequest
from onegov.core.utils import batched, PostThread
from onegov.server import Application as ServerApplication
from onegov.server.utils import load_class
from operator import itemgetter
from psycopg2.extensions import TransactionRollbackError
from purl import URL
from sqlalchemy.exc import OperationalError
from urllib.parse import urlencode
from webob.exc import HTTPConflict, HTTPServiceUnavailable


from typing import overload, Any, Literal, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import StrPath
    from _typeshed.wsgi import WSGIApplication, WSGIEnvironment, StartResponse
    from collections.abc import Callable, Iterable
    from email.headerregistry import Address
    from fs.base import FS, SubFS
    from gettext import GNUTranslations
    from morepath.request import Request
    from morepath.settings import SettingRegistry
    from sqlalchemy.orm import Session
    from translationstring import _ChameleonTranslate
    from typing_extensions import ParamSpec
    from webob import Response

    from .analytics import AnalyticsProvider
    from .mail import Attachment
    from .metadata import Metadata
    from .security.permissions import Intent
    from .types import EmailJsonDict, SequenceOrScalar

    _P = ParamSpec('_P')

_T = TypeVar('_T')

# Monkey patch
# https://linear.app/onegovcloud/issue/OGC-853/404-navigation-js-fehler
# This should be in more.webassets:
# https://github.com/morepath/more.webassets/blob/master/more/webassets/core.py#L55
if not WebassetsApp.dectate._directives[0][0].kw:
    from morepath.core import excview_tween_factory  # type:ignore
    WebassetsApp.dectate._directives[0][0].kw['over'] = excview_tween_factory


class Framework(
    TransactionApp,
    WebassetsApp,
    OrmCacheApp,
    ContentSecurityApp,
    ServerApplication,
):
    """ Baseclass for Morepath OneGov applications. """

    request_class: type[Request] = CoreRequest

    #: holds the database connection string, *if* there is a database connected
    dsn: str | None = None

    #: holdes the current schema associated with the database connection, set
    #: by and derived from :meth:`set_application_id`.
    # NOTE: Since this should almost always be set, we pretent it is always
    #       set to save ourselves the pain of having to check it everywhere
    schema: str = None  # type:ignore[assignment]

    #: framework directives
    form = directive(directives.HtmlHandleFormAction)
    cronjob = directive(directives.CronjobAction)
    analytics_provider = directive(directives.AnalyticsProviderAction)
    static_directory = directive(directives.StaticDirectoryAction)
    template_variables = directive(directives.TemplateVariablesAction)
    replace_setting = directive(directives.ReplaceSettingAction)
    replace_setting_section = directive(directives.ReplaceSettingSectionAction)

    #: sets the same-site cookie directive, (may need removal inside iframes)
    same_site_cookie_policy: str | None = 'Lax'

    #: the request cache is initialised/emptied before each request
    request_cache: dict[str, Any]

    #: the schema cache stays around for the entire runtime of the
    #: application, but is switched, each time the schema changes
    # NOTE: This cache should never be used to store ORM objects
    #       In addition this should generally be backed by a Redis
    #       cache to make sure the cache is synchronized between
    #       all processes. Although there may be some cases where
    #       it makes sense to use this cache on its own
    schema_cache: dict[str, Any]
    _all_schema_caches: dict[str, Any]

    @property
    def version(self) -> str:
        from onegov.core import __version__
        return __version__

    if TYPE_CHECKING:
        # this avoids us having to ignore a whole bunch of errors
        def __call__(
            self,
            environ: WSGIEnvironment,
            start_response: StartResponse
        ) -> Iterable[bytes]: ...

    @morepath.reify  # type:ignore[no-redef]
    def __call__(self) -> WSGIApplication:
        """ Intercept all wsgi calls so we can attach debug tools. """

        fn: WSGIApplication = super().__call__
        fn = self.with_print_exceptions(fn)
        fn = self.with_request_cache(fn)

        if getattr(self, 'sql_query_report', False):
            fn = self.with_query_report(fn)

        if getattr(self, 'profile', False):
            fn = self.with_profiler(fn)

        if getattr(self, 'with_sentry_middleware', False):
            from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware
            fn = SentryWsgiMiddleware(fn)

        return fn

    def with_query_report(self, fn: Callable[_P, _T]) -> Callable[_P, _T]:

        @wraps(fn)
        def with_query_report_wrapper(
            *args: _P.args,
            **kwargs: _P.kwargs
        ) -> _T:

            assert isinstance(self.sql_query_report, str)
            with debug.analyze_sql_queries(self.sql_query_report):
                return fn(*args, **kwargs)

        return with_query_report_wrapper

    def with_profiler(self, fn: Callable[_P, _T]) -> Callable[_P, _T]:

        @wraps(fn)
        def with_profiler_wrapper(
            *args: _P.args,
            **kwargs: _P.kwargs
        ) -> _T:
            filename = '{:%Y-%m-%d %H:%M:%S}.profile'.format(datetime.now())

            with utils.profile(filename):
                return fn(*args, **kwargs)

        return with_profiler_wrapper

    def with_request_cache(self, fn: Callable[_P, _T]) -> Callable[_P, _T]:

        @wraps(fn)
        def with_request_cache_wrapper(
            *args: _P.args,
            **kwargs: _P.kwargs
        ) -> _T:
            self.clear_request_cache()
            return fn(*args, **kwargs)

        return with_request_cache_wrapper

    def with_print_exceptions(
        self,
        fn: Callable[_P, _T]
    ) -> Callable[_P, _T]:

        @wraps(fn)
        def with_print_exceptions_wrapper(
            *args: _P.args,
            **kwargs: _P.kwargs
        ) -> _T:
            try:
                return fn(*args, **kwargs)
            except Exception:
                if getattr(self, 'print_exceptions', False):
                    print('=' * 80, file=sys.stderr)  # noqa: T201
                    traceback.print_exc()
                raise

        return with_print_exceptions_wrapper

    def clear_request_cache(self) -> None:
        self.request_cache = {}

    # FIXME: This is really bad for static type checking, we need to be
    #        really vigilant to import the actual module in TYPE_CHECKING
    #        everywhere we use this, so we're not operating on a bunch of
    #        Any types...
    @cached_property
    def modules(self) -> utils.Bunch:
        """ Provides access to modules used by the Framework class. Those
        modules cannot be included at the top because they themselves usually
        include the Framework.

        Admittelty a bit of a code smell.

        """
        from onegov.core import browser_session
        from onegov.core import cronjobs
        from onegov.core import filestorage
        from onegov.core import i18n
        from onegov.core import metadata
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
            theme=theme,
            metadata=metadata,
        )

    @property
    def metadata(self) -> Metadata:
        return self.modules.metadata.Metadata(self)

    @property
    def has_database_connection(self) -> bool:
        """ onegov.core has good integration for Postgres using SQLAlchemy, but
        it doesn't require a connection.

        It's possible to have Onegov applications using a different database
        or not using one at all.

        """
        return self.dsn is not None

    @property
    def has_filestorage(self) -> bool:
        """ Returns true if :attr:`fs` is available. """
        return self._global_file_storage is not None

    def handle_exception(
        self,
        exception: BaseException,
        environ: WSGIEnvironment,
        start_response: StartResponse
    ) -> Iterable[bytes]:
        """ Stops database connection errors from bubbling all the way up
        to our exception handling services (sentry.io).

        """

        if isinstance(exception, DB_CONNECTION_ERRORS):
            return HTTPServiceUnavailable()(environ, start_response)

        return super().handle_exception(exception, environ, start_response)

    # TODO: Add annotations for the known configuration options?
    def configure_application(self, **cfg: Any) -> None:
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

        :redis_url:
            The redis url used (default is 'redis://localhost:6379/0').

        :file_storage:
            The file_storage module to use. See
            `<https://docs.pyfilesystem.org/en/latest/filesystems.html>`_

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
            key=itemgetter(0)
        )

        for n, method in members:
            if n.startswith('configure_') and n != 'configure_application':
                method(self, **cfg)

    def configure_dsn(
        self,
        *,
        dsn: str | None = None,
        # FIXME: Use sqlalchemy.orm.DeclarativeBase once we switch to 2.0
        base: type[Any] = Base,
        **cfg: Any
    ) -> None:

        # certain namespaces are reserved for internal use:
        assert self.namespace != 'global'

        self.dsn = dsn

        if self.dsn:
            self.session_manager = SessionManager(self.dsn, base)
            # NOTE: We used to only add the ORMBase, when we derived
            #       from LibresIntegration, however this leads to
            #       issues when we add a backref from a model derived
            #       from ORMBase to a model like File, since SQLAlchemy
            #       will try to load this backref when inspecting
            #       the state of an instance and fail, because the
            #       referenced table doesn't exist
            self.session_manager.bases.append(ORMBase)

    def configure_redis(
        self,
        *,
        redis_url: str = 'redis://127.0.0.1:6379/0',
        **cfg: Any
    ) -> None:

        self.redis_url = redis_url

    def configure_secrets(
        self,
        *,
        identity_secure: bool = True,
        identity_secret: str | None = None,
        csrf_secret: str | None = None,
        csrf_time_limit: float = 1200,
        **cfg: Any
    ) -> None:

        self.identity_secure = identity_secure

        # the identity secret is shared between tennants, so we name it
        # accordingly - use self.identity_secret to get a secret limited to
        # the current tennant
        self.unsafe_identity_secret = (
            identity_secret
            or stored_random_token(self.__class__.__name__, 'identity_secret'))

        # same goes for the csrf_secret
        self.unsafe_csrf_secret = (
            csrf_secret
            or stored_random_token(self.__class__.__name__, 'csrf_secret'))

        self.csrf_time_limit = int(csrf_time_limit)

        # you don't want these keys to be the same, see docstring above
        assert self.unsafe_identity_secret != self.unsafe_csrf_secret

        # you don't want to use the keys given in the example file
        assert (
            self.unsafe_identity_secret != 'very-secret-key'  # nosec: B105
        )

        # you don't want to use the keys given in the example file
        assert (
            self.unsafe_csrf_secret != 'another-very-secret-key'  # nosec: B105
        )

    def configure_yubikey(
        self,
        *,
        yubikey_client_id: str | None = None,
        yubikey_secret_key: str | None = None,
        **cfg: Any
    ) -> None:

        self.yubikey_client_id = yubikey_client_id
        self.yubikey_secret_key = yubikey_secret_key

    def configure_mtan_second_factor(
        self,
        *,
        mtan_second_factor_enabled: bool = False,
        mtan_automatic_setup: bool = False,
        **cfg: Any
    ) -> None:

        self.mtan_second_factor_enabled = mtan_second_factor_enabled
        self.mtan_automatic_setup = mtan_automatic_setup

    def configure_totp(
        self,
        *,
        totp_enabled: bool = True,
        **cfg: Any
    ) -> None:

        self.totp_enabled = totp_enabled

    def configure_filestorage(self, **cfg: Any) -> None:

        if 'filestorage_object' in cfg:
            self._global_file_storage = cfg['filestorage_object']
            return

        if 'filestorage' in cfg:
            filestorage_class = load_class(cfg['filestorage'])
            filestorage_options = cfg.get('filestorage_options', {})

            # legacy support for pyfilesystem 1.x parameters
            if 'dir_mode' in filestorage_options:
                filestorage_options['create_mode'] = (
                    filestorage_options.pop('dir_mode'))
        else:
            filestorage_class = None

        if filestorage_class:
            self._global_file_storage = filestorage_class(
                **filestorage_options)
        else:
            self._global_file_storage = None

    def configure_debug(
        self,
        *,
        always_compile_theme: bool = False,
        allow_shift_f5_compile: bool = False,
        sql_query_report: Literal[
            False, 'summary', 'redundant', 'all'] = False,
        profile: bool = False,
        print_exceptions: bool = False,
        **cfg: Any
    ) -> None:

        self.always_compile_theme = always_compile_theme
        self.allow_shift_f5_compile = allow_shift_f5_compile
        self.sql_query_report = sql_query_report
        self.profile = profile
        self.print_exceptions = print_exceptions

    # TODO: Add TypedDict for mail config
    def configure_mail(
        self,
        *,
        mail: dict[str, Any] | None = None,
        **cfg: Any
    ) -> None:

        self.mail = mail
        if self.mail:
            assert isinstance(self.mail, dict)
            assert 'transactional' in self.mail
            assert 'marketing' in self.mail

    def configure_sms(
        self,
        *,
        sms_directory: str | None = None,  # deprecated
        sms: dict[str, Any] | None = None,
        **cfg: Any
    ) -> None:

        self.sms = sms or {'directory': sms_directory}
        self.sms_directory = self.sms['directory']

    def configure_hipchat(
        self,
        *,
        hipchat_token: str | None = None,
        hipchat_room_id: str | None = None,
        **cfg: Any
    ) -> None:

        self.hipchat_token = hipchat_token
        self.hipchat_room_id = hipchat_room_id

    def configure_zulip(
        self,
        *,
        zulip_url: str | None = None,
        zulip_stream: str | None = None,
        zulip_user: str | None = None,
        zulip_key: str | None = None,
        **cfg: Any
    ) -> None:

        self.zulip_url = zulip_url
        self.zulip_stream = zulip_stream
        self.zulip_user = zulip_user
        self.zulip_key = zulip_key

    def configure_content_security_policy(
        self,
        *,
        content_security_policy_enabled: bool = True,
        content_security_policy_report_uri: str | None = None,
        content_security_policy_report_only: bool = False,
        content_security_policy_report_sample_rate: float = 0.0,
        content_security_policy_extra_script_src: list[str] | None = None,
        **cfg: Any
    ) -> None:

        self.content_security_policy_enabled = content_security_policy_enabled
        self.content_security_policy_report_uri = (
            content_security_policy_report_uri)
        self.content_security_policy_report_only = (
            content_security_policy_report_only)
        self.content_security_policy_report_sample_rate = (
            content_security_policy_report_sample_rate)
        self.content_security_policy_extra_script_src = (
            content_security_policy_extra_script_src or []
        )

    def configure_sentry(
        self,
        *,
        sentry_dsn: str | None = None,
        **cfg: Any
    ) -> None:

        self.sentry_dsn = sentry_dsn

    @property
    def is_sentry_supported(self) -> bool:
        return getattr(self, 'sentry_dsn', None) and True or False

    def configure_analytics_providers(self, **cfg: Any) -> None:
        self.analytics_providers_configs = cfg.get('analytics_providers', {})

    @cached_property
    def available_analytics_providers(self) -> dict[str, AnalyticsProvider]:
        return {
            name: provider
            for name, _provider_cfg in self.analytics_providers_configs.items()
            if (cls := self.config.analytics_provider_registry.get(
                (provider_cfg := _provider_cfg or {}).get('provider', name)
            )) is not None
            if (
                provider := cls.configure(name=name, **provider_cfg)
            ) is not None
        }

    def set_application_id(self, application_id: str) -> None:
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
        if not hasattr(self, '_all_schema_caches'):
            self._all_schema_caches = {}

        self.schema_cache = self._all_schema_caches.setdefault(self.schema, {})

        if self.has_database_connection:
            ScopedPropertyObserver.enter_scope(self)

            self.session_manager.set_current_schema(self.schema)

            if not self.is_orm_cache_setup:
                self.setup_orm_cache()

    def get_cache(
        self,
        name: str,
        expiration_time: float
    ) -> cache.RedisCacheRegion:
        """ Gets a cache bound to this application id. """
        return cache.get(
            namespace=f'{self.application_id}:{name}',
            expiration_time=expiration_time,
            redis_url=self.redis_url
        )

    @property
    def session_cache(self) -> cache.RedisCacheRegion:
        """ A cache that is kept for a long-ish time. """
        day = 60 * 60 * 24
        return self.get_cache('sessions', expiration_time=7 * day)

    @property
    def cache(self) -> cache.RedisCacheRegion:
        """ A cache that might be invalidated frequently. """
        return self.get_cache('short-term', expiration_time=3600)

    @property
    def settings(self) -> SettingRegistry:
        return self.config.setting_registry

    @property
    def application_id_hash(self) -> str:
        """ The application_id as hash, use this if the application_id can
        be read by the user -> this obfuscates things slightly.

        """
        # sha-1 should be enough, because even if somebody was able to get
        # the cleartext value I honestly couldn't tell you what it could be
        # used for...
        return hashlib.new(  # nosec: B324
            'sha1',
            self.application_id.encode('utf-8'),
            usedforsecurity=False
        ).hexdigest()

    @overload
    def object_by_path(
        self,
        path: str,
        with_view_name: Literal[False] = ...
    ) -> object | None: ...

    @overload
    def object_by_path(
        self,
        path: str,
        with_view_name: Literal[True]
    ) -> tuple[object | None, str | None]: ...

    def object_by_path(
        self,
        path: str,
        with_view_name: bool = False
    ) -> object | tuple[object | None, str | None] | None:
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

    def permission_by_view(
        self,
        model: type[object] | object,
        view_name: str | None = None
    ) -> type[Intent]:
        """ Returns the permission required for the given model and view_name.

        The model may be an instance or a class.

        If the view cannot be evaluated, a KeyError is raised.

        """
        assert model is not None

        model = model if inspect.isclass(model) else model.__class__
        predicates = {'name': view_name} if view_name else {}

        query = dectate.Query('view').filter(
            model=model,
            predicates=predicates
        )

        try:
            action, _handler = next(query(self.__class__))
        except (StopIteration, RuntimeError) as exception:
            raise KeyError(
                '{!r} has no view named {}'.format(model, view_name)
            ) from exception

        return action.permission

    @cached_property
    def session(self) -> Callable[[], Session]:
        """ Alias for self.session_manager.session. """
        return self.session_manager.session

    def send_marketing_email(
        self,
        reply_to: Address | str | None = None,
        receivers: SequenceOrScalar[Address | str] = (),
        cc: SequenceOrScalar[Address | str] = (),
        bcc: SequenceOrScalar[Address | str] = (),
        subject: str | None = None,
        content: str | None = None,
        attachments: Iterable[Attachment | StrPath] = (),
        headers: dict[str, str] | None = None,
        plaintext: str | None = None
    ) -> None:
        """ Sends an e-mail categorised as marketing.

        This includes but is not limited to:

            * Announcements
            * Newsletters
            * Promotional E-Mails

        When in doubt, send a marketing e-mail. Transactional e-mails are
        sacred and should only be used if necessary. This ensures that the
        important stuff is reaching our customers!

        However, marketing emails will always need to contain an unsubscribe
        link in the email body and in a List-Unsubscribe header.

        """
        return self.send_email(
            reply_to=reply_to,
            category='marketing',
            receivers=receivers,
            cc=cc,
            bcc=bcc,
            subject=subject,
            content=content,
            attachments=attachments,
            headers=headers,
            plaintext=plaintext
        )

    def send_marketing_email_batch(
        self,
        prepared_emails: Iterable[EmailJsonDict]
    ) -> None:
        """ Sends an e-mail batch categorised as marketing.

        This includes but is not limited to:

            * Announcements
            * Newsletters
            * Promotional E-Mails

        When in doubt, send a marketing e-mail. Transactional e-mails are
        sacred and should only be used if necessary. This ensures that the
        important stuff is reaching our customers!

        However, marketing emails will always need to contain an unsubscribe
        link in the email body and in a List-Unsubscribe header.

        :param prepared_emails: A list of emails prepared using
            app.prepare_email

        Supplying anything other than stream='marketing' in prepare_email
        will be considered an error.

        Batches will be split automatically according to API limits.

        """
        return self.send_email_batch(prepared_emails, category='marketing')

    def send_transactional_email(
        self,
        reply_to: Address | str | None = None,
        receivers: SequenceOrScalar[Address | str] = (),
        cc: SequenceOrScalar[Address | str] = (),
        bcc: SequenceOrScalar[Address | str] = (),
        subject: str | None = None,
        content: str | None = None,
        attachments: Iterable[Attachment | StrPath] = (),
        headers: dict[str, str] | None = None,
        plaintext: str | None = None
    ) -> None:
        """ Sends an e-mail categorised as transactional.

        This is limited to:

            * Welcome emails
            * Reset passwords emails
            * Notifications
            * Weekly digests
            * Receipts and invoices

        """
        return self.send_email(
            reply_to=reply_to,
            category='transactional',
            receivers=receivers,
            cc=cc,
            bcc=bcc,
            subject=subject,
            content=content,
            attachments=attachments,
            headers=headers,
            plaintext=plaintext
        )

    def send_transactional_email_batch(
        self,
        prepared_emails: Iterable[EmailJsonDict]
    ) -> None:
        """  Sends an e-mail categorised as transactional.

        This is limited to:

            * Welcome emails
            * Reset passwords emails
            * Notifications
            * Weekly digests
            * Receipts and invoices

        :param prepared_emails: A list of emails prepared using
            app.prepare_email

        Supplying anything other than stream='transactional' in prepare_email
        will be considered an error.

        Batches will be split automatically according to API limits.

        """
        return self.send_email_batch(prepared_emails, category='transactional')

    def prepare_email(
        self,
        reply_to: Address | str | None = None,
        category: Literal['marketing', 'transactional'] = 'marketing',
        receivers: SequenceOrScalar[Address | str] = (),
        cc: SequenceOrScalar[Address | str] = (),
        bcc: SequenceOrScalar[Address | str] = (),
        subject: str | None = None,
        content: str | None = None,
        attachments: Iterable[Attachment | StrPath] = (),
        headers: dict[str, str] | None = None,
        plaintext: str | None = None
    ) -> EmailJsonDict:
        """ Common path for batch and single mail sending. Use this the same
        way you would use send_email then pass the prepared emails in a list
        or another iterable to the batch send method.
        """

        headers = headers or {}
        assert reply_to
        assert category in ('transactional', 'marketing')
        assert self.mail is not None
        sender = self.mail[category]['sender']
        assert sender

        # Postmark requires E-Mails in the marketing stream to contain
        # a List-Unsubscribe header
        assert category != 'marketing' or 'List-Unsubscribe' in headers

        # transactional stream in Postmark is called outbound
        stream = 'marketing' if category == 'marketing' else 'outbound'
        email = prepare_email(
            sender=sender,
            reply_to=reply_to,
            receivers=receivers,
            cc=cc,
            bcc=bcc,
            subject=subject,
            content=content,
            attachments=attachments,
            stream=stream,
            headers=headers,
            plaintext=plaintext
        )

        # Postmark requires emails in the marketing stream to contain
        # an unsubscribe link in the email content.
        if category == 'marketing':
            link = headers['List-Unsubscribe'].strip('<>')
            assert link in email['TextBody']
            assert 'HtmlBody' not in email or link in email['HtmlBody']

        return email

    def send_email(
        self,
        reply_to: Address | str | None = None,
        category: Literal['marketing', 'transactional'] = 'marketing',
        receivers: SequenceOrScalar[Address | str] = (),
        cc: SequenceOrScalar[Address | str] = (),
        bcc: SequenceOrScalar[Address | str] = (),
        subject: str | None = None,
        content: str | None = None,
        attachments: Iterable[Attachment | StrPath] = (),
        headers: dict[str, str] | None = None,
        plaintext: str | None = None
    ) -> None:
        """ Sends a plain-text e-mail to the given recipients. A reply to
        address is used to enable people to answer to the e-mail which is
        usually sent by a noreply kind of e-mail address.

        E-mails sent through this method are bound to the current transaction.
        If that transaction is aborted or not commited, the e-mail is not sent.

        Usually you'll use this method inside a request, where transactions
        are automatically commited at the end.

        """
        assert self.mail is not None
        headers = headers or {}
        directory = self.mail[category]['directory']
        assert directory

        # most of the validation happens inside prepare_email
        # so the send_email signature looks more lax than it
        # actually is, so applications only need to overwrite
        # prepare_email to replace required arguments with
        # optional arguments with a static default value.
        # this also allows consistent behavior between single
        # and batch emails.

        # currently we send even single emails with the batch
        # endpoint to simplify the queue processing, so we pack
        # the single message into a list
        payload = json.dumps([self.prepare_email(
            reply_to=reply_to,
            receivers=receivers,
            cc=cc,
            bcc=bcc,
            subject=subject,
            content=content,
            attachments=attachments,
            category=category,
            headers=headers,
            plaintext=plaintext
        )]).encode('utf-8')

        # Postmark API Limit
        assert len(payload) <= 50_000_000

        dest_path = os.path.join(
            directory, '0.1.{}'.format(datetime.now().timestamp())
        )

        # send e-mails through the transaction machinery
        FileDataManager.write_file(payload, dest_path)

    def send_email_batch(
        self,
        prepared_emails: Iterable[EmailJsonDict],
        category: Literal['marketing', 'transactional'] = 'marketing'
    ) -> None:
        """ Sends an e-mail batch.

        :param prepared_emails: A list of emails prepared using
            app.prepare_email

        Batches will be split automatically according to API limits.

        """

        assert self.mail is not None
        directory = self.mail[category]['directory']
        assert directory

        # transactional stream in Postmark is called outbound
        stream = 'marketing' if category == 'marketing' else 'outbound'

        BATCH_LIMIT = 500  # noqa: N806
        # NOTE: The API specifies MB, so let's not chance it
        #       by assuming they meant MiB and just go with
        #       lower size limit.
        SIZE_LIMIT = 50_000_000  # 50MB  # noqa: N806
        # NOTE: We use a buffer to be a bit more memory efficient
        #       we don't initialize the buffer, so tell gives us
        #       the exact size of the buffer.
        buffer = io.BytesIO()
        buffer.write(b'[')
        num_included = 0
        batch_num = 0
        timestamp = datetime.now().timestamp()

        def finish_batch() -> None:
            nonlocal buffer, num_included, batch_num

            buffer.write(b']')

            # if the batch is empty we just skip it
            if num_included > 0:
                assert num_included <= BATCH_LIMIT
                assert buffer.tell() <= SIZE_LIMIT
                dest_path = os.path.join(
                    directory, '{}.{}.{}'.format(
                        batch_num, num_included, timestamp
                    )
                )

                # send e-mails through the transaction machinery
                FileDataManager.write_file(buffer.getvalue(), dest_path)
                batch_num += 1

            # prepare vars for next batch
            buffer.close()
            buffer = io.BytesIO()
            buffer.write(b'[')
            num_included = 0

        for email in prepared_emails:
            assert email['MessageStream'] == stream
            # TODO: we could verify that From is the correct
            #       sender for the category...

            payload = json.dumps(email).encode('utf-8')
            if buffer.tell() + len(payload) >= SIZE_LIMIT:
                finish_batch()

            if num_included:
                buffer.write(b',')

            buffer.write(payload)
            num_included += 1

            if num_included == BATCH_LIMIT:
                finish_batch()

        # finish final partially full batch
        finish_batch()

    @property
    def can_deliver_sms(self) -> bool:
        """ Returns whether or not the current schema is configured for
        SMS delivery.

        """
        if not self.sms_directory:
            return False

        if self.sms.get('user'):
            return True

        tenants = self.sms.get('tenants', None)
        if tenants is None:
            return False

        cfg = tenants.get(self.application_id)
        if cfg is None:
            cfg = tenants.get(self.namespace)

        return cfg is not None and cfg.get('user')

    def send_sms(
        self,
        receivers: SequenceOrScalar[str],
        content: str | bytes
    ) -> None:
        """ Sends an SMS by writing a file to the `sms_directory` of the
        principal.

        receivers can be a single phone number or a collection of numbers.
        Delivery will be split into multiple batches if the number of receivers
        exceeds 1000, this is due to a limit in the ASPSMS API. This also means
        more than one file is written in such cases. They will share the same
        timestamp but will have a batch number prefixed.

        SMS sent through this method are bound to the current transaction.
        If that transaction is aborted or not commited, the SMS is not sent.

        Usually you'll use this method inside a request, where transactions
        are automatically commited at the end.

        """
        assert self.sms_directory, 'No SMS directory configured'

        path = os.path.join(self.sms_directory, self.schema)
        if not os.path.exists(path):
            os.makedirs(path)

        tmp_path = os.path.join(self.sms_directory, 'tmp')
        if not os.path.exists(tmp_path):
            os.makedirs(tmp_path)

        if isinstance(receivers, str):
            receivers = [receivers]

        if isinstance(content, bytes):
            # NOTE: This will fail if we want to be able to send
            #       arbitrary bytes. We could put an errors='ignore'
            #       on this. But it's probably better if we fail.
            #       If we need to be able to send arbitrary bytes
            #       we would need to encode the content in some
            #       other way, e.g. base64, but since ASPSMS is a
            #       JSON API this probably is not possible anyways.
            content = content.decode('utf-8')

        timestamp = datetime.now().timestamp()

        for index, receiver_batch in enumerate(batched(receivers, 1000)):
            payload = json.dumps({
                'receivers': receiver_batch,
                'content': content
            }).encode('utf-8')

            dest_path = os.path.join(
                path, f'{index}.{len(receiver_batch)}.{timestamp}'
            )

            tmp_dest_path = os.path.join(
                tmp_path,
                f'{self.schema}-{index}.{len(receiver_batch)}.{timestamp}'
            )

            FileDataManager.write_file(payload, dest_path, tmp_dest_path)

    def send_zulip(self, subject: str, content: str) -> PostThread | None:
        """ Sends a zulip chat message asynchronously.

        We are using the stream message method of zulip:
        `<https://zulipchat.com/api/stream-message>`_

        Returns the thread object to allow waiting by calling join.

        """

        if not self.zulip_url:
            return None

        if not self.zulip_stream:
            return None

        if not self.zulip_user:
            return None

        if not self.zulip_key:
            return None

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
            ('Authorization', 'Basic {}'.format(auth.decode('ascii'))),
            ('Content-Type', 'application/x-www-form-urlencoded'),
            ('Content-Length', str(len(data))),
        )

        thread = PostThread(self.zulip_url, data, headers)
        thread.start()

        return thread

    @cached_property
    def static_files(self) -> list[str]:
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
    def serve_static_files(self) -> bool:
        """ Returns True if ``/static`` files should be served. Needs to be
        enabled manually.

        Note that even if the static files are not served, ``/static`` path
        is still served, it just won't return anything but a 404.

        Note also that static files are served **publicly**. You can override
        this in your application, but doing that and testing for it is on you!

        See also: :mod:`onegov.core.static`. """
        return False

    def application_bound_identity(
        self,
        userid: str,
        uid: str,
        groupids: frozenset[str],
        role: str
    ) -> morepath.authentication.Identity:
        """ Returns a new morepath identity for the given userid, group and
        role, bound to this application.

        """
        return morepath.authentication.Identity(
            userid, uid=uid, groupids=groupids, role=role,
            application_id=self.application_id_hash
        )

    @property
    def filestorage(self) -> SubFS[FS] | None:
        """ Returns a filestorage object bound to the current application.
        Based on this nifty module:

        `<https://docs.pyfilesystem.org/en/latest/>`_

        The file storage returned is guaranteed to be independent of other
        applications (the scope is the application_id, not just the class).

        There is no guarantee as to what file storage backend is actually used.
        It's quite possible that the file storage will be somewhere online
        in the future (e.g. S3).

        Therefore, the urls for the file storage should always be acquired
        through :meth:`onegov.core.request.CoreRequest.filestorage_link`.

        The backend is configured through :meth:`configure_application`.

        For a list of methods available on the resulting object, consult this
        list: `<https://docs.pyfilesystem.org/en/latest/interface.html>`_.

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
            app.filestorage.writetext(filename, 'Lorem Ipsum')

            # returns either an url like '/files/4ec56cc005c594880a...'
            # or maybe 'https://amazonaws.com/onegov-cloud/32746/220592/q...'
            request.filestorage_link(filename)

        """
        if self._global_file_storage is None:
            return None

        assert self.schema is not None
        return utils.makeopendir(self._global_file_storage, self.schema)

    @property
    def themestorage(self) -> SubFS[FS] | None:
        """ Returns a storage object meant for themes, shared by all
        applications.

        Only use this for theming, nothing else!

        """

        if self._global_file_storage is None:
            return None

        return utils.makeopendir(self._global_file_storage, 'global-theme')

    @property
    def theme_options(self) -> dict[str, Any]:
        """ Returns the application-bound theme options. """
        return {}

    @cached_property
    def translations(self) -> dict[str, GNUTranslations]:
        """ Returns all available translations keyed by language. """

        try:
            if not self.settings.i18n.localedirs:
                return {}

            return self.modules.i18n.get_translations(
                self.settings.i18n.localedirs
            )
        except AttributeError:
            return {}

    @cached_property
    def chameleon_translations(self) -> dict[str, _ChameleonTranslate]:
        """ Returns all available translations for chameleon. """
        return self.modules.i18n.wrap_translations_for_chameleon(
            self.translations
        )

    @cached_property
    def locales(self) -> set[str]:
        """ Returns all available locales in a set. """
        try:
            if self.settings.i18n.locales:
                return self.settings.i18n.locales
        except AttributeError:
            pass

        return set(self.translations.keys())

    @cached_property
    def default_locale(self) -> str | None:
        """ Returns the default locale. """
        try:
            if self.settings.i18n.default_locale:
                return self.settings.i18n.default_locale
        except AttributeError:
            pass
        return None

    @property
    def identity_secret(self) -> str:
        """ The identity secret, guaranteed to only be valid for the current
        application id.

        """
        return HKDF(
            algorithm=SHA256(),
            length=32,
            # NOTE: salt should generally be left blank or use pepper
            #       the better way to provide salt is to add it to info
            #       see: https://soatok.blog/2021/11/17/understanding-hkdf/
            salt=None,
            info=self.application_id.encode('utf-8') + b'+identity'
        ).derive(
            self.unsafe_identity_secret.encode('utf-8')
        ).hex()

    @property
    def csrf_secret(self) -> str:
        """ The identity secret, guaranteed to only be valid for the current
        application id.

        """
        return HKDF(
            algorithm=SHA256(),
            length=32,
            # NOTE: salt should generally be left blank or use pepper
            #       the better way to provide salt is to add it to info
            #       see: https://soatok.blog/2021/11/17/understanding-hkdf/
            salt=None,
            info=self.application_id.encode('utf-8') + b'+csrf'
        ).derive(
            self.unsafe_csrf_secret.encode('utf-8')
        ).hex()

    def sign(self, text: str, salt: str = 'generic-signer') -> str:
        """ Signs a text with the identity secret.

        The text is signed together with the application id, so if one
        application signs a text another won't be able to unsign it.

        """
        signer = Signer(self.identity_secret, salt=salt)
        return signer.sign(text.encode('utf-8')).decode('utf-8')

    def unsign(self, text: str, salt: str = 'generic-signer') -> str | None:
        """ Unsigns a signed text, returning None if unsuccessful. """
        try:
            signer = Signer(self.identity_secret, salt=salt)
            return signer.unsign(text).decode('utf-8')
        except BadSignature:
            return None

    @property
    def hashed_identity_key(self) -> bytes:
        """ Take the sha-256 because we want a key that is 32 bytes long. """
        hash_object = hashlib.sha256()
        hash_object.update(self.identity_secret.encode('utf-8'))
        return b64encode(hash_object.digest())

    def encrypt(self, plaintext: str) -> bytes:
        """ Encrypts the given text using Fernet (symmetric encryption).

        plaintext (str): The data to encrypt.

        Returns: the encrypted data in bytes.
        """
        return Fernet(
            self.hashed_identity_key
        ).encrypt(plaintext.encode('utf-8'))

    def decrypt(self, cyphertext: bytes) -> str:
        """ Decrypts the given text using Fernet (symmetric encryption).

        cyphertext (str): The data to encrypt.

        Returns: the decrypted text.
        """
        return Fernet(
            self.hashed_identity_key
        ).decrypt(cyphertext).decode('utf-8')

    @dispatch_method('model')
    def get_layout_class(self, model: object) -> type | None:
        return None


@Framework.predicate(Framework.get_layout_class, name='model', default=None, index=ClassIndex)
def model_predicate(self, model: object) -> type:
    # return model if isinstance(model, type) else model.__class__
    retval = model if isinstance(model, type) else model.__class__
    print('*** tschupre model predicate called for object:', model, 'retval:', retval)
    return retval


@Framework.webasset_url()
def get_webasset_url() -> str:
    """ The webassets url needs to be unique so we can fix it before
    returning the generated html. See :func:`fix_webassets_url_factory`.

    """
    return '7da9c72a3b5f9e060b898ef7cd714b8a'  # do *not* change this hash!


@Framework.webasset_filter('js')
def get_js_filter() -> str:
    return 'rjsmin'


@Framework.webasset_filter('css')
def get_css_filter() -> str:
    return 'custom-rcssmin'


@Framework.webasset_filter('jsx', produces='js')
def get_jsx_filter() -> str:
    return 'jsx'


@Framework.tween_factory(over=webassets_injector_tween)
def fix_webassets_url_factory(
    app: Framework,
    handler: Callable[[CoreRequest], Response]
) -> Callable[[CoreRequest], Response]:
    def fix_webassets_url(request: CoreRequest) -> Response:
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
def get_retry_attempts() -> int:
    return 2


@Framework.setting(section='cronjobs', name='enabled')
def get_cronjobs_enabled() -> bool:
    """ If this value is set to False, all cronjobs are disabled. Only use
    this during testing. Cronjobs have no impact on your application, unless
    there are defined cronjobs, in which case they are there for a reason.

    """
    return True


@Framework.setting(section='content_security_policy', name='default')
def default_content_security_policy() -> ContentSecurityPolicy:
    """ The default content security policy used throughout OneGov. """

    return ContentSecurityPolicy(
        # by default limit to self
        default_src={SELF},

        # allow fonts from practically anywhere (no mixed content though)
        font_src={SELF, 'http:', 'https:', 'data:'},

        # allow images from practically anywhere (no mixed content though)
        img_src={SELF, 'http:', 'https:', 'data:'},

        # enable inline styles and external stylesheets
        style_src={SELF, 'https:', UNSAFE_INLINE},

        # enable inline scripts and external scripts for sentry
        script_src={
            SELF,
            'https://browser.sentry-cdn.com',
            'https://js.sentry-cdn.com',
        },

        # by default limit to self (allow pdf viewer etc)
        object_src={NONE},

        # only allow setting <base> to self
        base_uri={SELF},

        # only allow submitting forms to self
        form_action={SELF},

        # disable all mixed content (https -> http)
        block_all_mixed_content=True,

        connect_src={SELF, '*.sentry.io'}
    )


@Framework.setting(section='content_security_policy', name='apply_policy')
def default_policy_apply_factory(
) -> Callable[[ContentSecurityPolicy, CoreRequest, Response], None]:
    """ Adds the content security policy report settings from the yaml. """

    def apply_policy(
        policy: ContentSecurityPolicy,
        request: CoreRequest,
        response: Response
    ) -> None:

        if not request.app.content_security_policy_enabled:
            return

        sample_rate = request.app.content_security_policy_report_sample_rate
        report_only = request.app.content_security_policy_report_only

        if random.uniform(0, 1) <= sample_rate:  # nosec B311
            report_uri = request.app.content_security_policy_report_uri
        else:
            report_uri = None

        policy.report_uri = report_uri or ''
        policy.report_only = report_only

        if script_srcs := request.app.content_security_policy_extra_script_src:
            # NOTE: We don't want to modify the original CSP
            #       we don't care with report_uri and report_only
            #       since we set it for every request, but if this
            #       setting changes we would no longer produce the
            #       correct CSP, if we modified it previously.
            policy = policy.copy()
            for script_src in script_srcs:
                policy.script_src.add(script_src)

        policy.apply(response)

    return apply_policy


@Framework.tween_factory(over=transaction_tween_factory)
def http_conflict_tween_factory(
    app: Framework,
    handler: Callable[[CoreRequest], Response]
) -> Callable[[CoreRequest], Response]:

    def http_conflict_tween(request: CoreRequest) -> Response:
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

            log.warning('A transaction failed because there was a conflict')

            return HTTPConflict()

    return http_conflict_tween


@Framework.tween_factory(over=transaction_tween_factory)
def activate_session_manager_factory(
    app: Framework,
    handler: Callable[[CoreRequest], Response]
) -> Callable[[CoreRequest], Response]:
    """ Activate the session manager before each transaction. """
    def activate_session_manager(request: CoreRequest) -> Response:
        if app.has_database_connection:
            request.app.session_manager.activate()

        return handler(request)

    return activate_session_manager


@Framework.tween_factory(over=transaction_tween_factory)
def close_session_after_request_factory(
    app: Framework,
    handler: Callable[[CoreRequest], Response]
) -> Callable[[CoreRequest], Response]:
    """ Closes the session after each request.

    This frees up connections that are unused, without costing us any
    request performance from what I can measure.

    """
    def close_session_after_request(request: CoreRequest) -> Response:
        try:
            return handler(request)
        finally:
            if app.has_database_connection:
                request.session.close()

    return close_session_after_request


@Framework.tween_factory(under=http_conflict_tween_factory)
def current_language_tween_factory(
    app: Framework,
    handler: Callable[[CoreRequest], Response]
) -> Callable[[CoreRequest], Response]:
    def current_language_tween(request: CoreRequest) -> Response:
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
def spawn_cronjob_thread_tween_factory(
    app: Framework,
    handler: Callable[[CoreRequest], Response]
) -> Callable[[CoreRequest], Response]:

    from onegov.core.cronjobs import ApplicationBoundCronjobs
    registry = app.config.cronjob_registry

    if not hasattr(registry, 'cronjobs'):
        return handler

    if not app.settings.cronjobs.enabled:
        return handler

    def spawn_cronjob_thread_tween(request: CoreRequest) -> Response:
        if app.application_id not in registry.cronjob_threads:
            thread = ApplicationBoundCronjobs(
                request, registry.cronjobs.values()
            )

            registry.cronjob_threads[request.app.application_id] = thread

            thread.start()

        return handler(request)

    return spawn_cronjob_thread_tween


@Framework.tween_factory(under=webassets_injector_tween)
def cache_control_tween_factory(
    app: Framework,
    handler: Callable[[CoreRequest], Response]
) -> Callable[[CoreRequest], Response]:

    def set_cache_control_header_tween(request: CoreRequest) -> Response:
        response = handler(request)
        if (
            (
                # logged in as a user
                request.is_logged_in
                # logged in as a citizen
                or getattr(request, 'authenticated_email', None)
            )
            # original headers take precedence
            and 'Cache-Control' not in response.headers
            # files have their own cache control handling
            and '/storage/' not in request.path
        ):
            response.headers['Cache-Control'] = 'no-store'
        return response

    return set_cache_control_header_tween
