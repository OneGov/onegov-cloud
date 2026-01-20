from __future__ import annotations

import morepath
import ua_parser

from datetime import timedelta
from functools import cached_property
from onegov.core.cache import instance_lru_cache
from onegov.core.custom import msgpack
from onegov.core.utils import append_query_param
from itsdangerous import (
    BadSignature,
    SignatureExpired,
    TimestampSigner,
    URLSafeSerializer,
    URLSafeTimedSerializer
)
from more.content_security import ContentSecurityRequest, UNSAFE_EVAL
from more.webassets.core import IncludeRequest
from morepath.authentication import NO_IDENTITY
from morepath.error import LinkError
from morepath.request import SAME_APP
from onegov.core import utils
from onegov.core.crypto import random_token
from webob.exc import HTTPForbidden
from wtforms.csrf.session import SessionCSRF


from typing import cast, overload, Any, NamedTuple, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsItems
    from collections.abc import Callable, Iterable, Iterator, Sequence
    from dectate import Sentinel
    from gettext import GNUTranslations
    from markupsafe import Markup
    from morepath import App
    from morepath.authentication import Identity, NoIdentity
    from onegov.core import Framework
    from onegov.core.browser_session import BrowserSession
    from onegov.core.i18n.translation_string import TranslationMarkup
    from onegov.core.security.permissions import Intent
    from onegov.core.types import MessageType
    from sqlalchemy import Column
    from sqlalchemy.orm import relationship, Session
    from translationstring import _ChameleonTranslate
    from typing import Literal, Protocol, TypeGuard
    from webob import Response
    from webob.multidict import MultiDict
    from webob.request import _FieldStorageWithFile
    from wtforms import Form
    from uuid import UUID

    from .analytics import AnalyticsProvider
    from .templates import TemplateLoader

    _BaseRequest = morepath.Request

    # NOTE: To avoid a dependency between onegov.core and onegov.user
    #       we use a UserLike Protocol to define the properties we need
    #       to be present on a user.
    class GroupLike(Protocol):
        @property
        def id(self) -> UUID | Column[UUID]: ...
        @property
        def name(self) -> str | Column[str | None] | None: ...

    class UserLike(Protocol):
        @property
        def id(self) -> UUID | Column[UUID]: ...
        @property
        def username(self) -> str | Column[str]: ...
        @property
        def groups(self) -> (
            Sequence[GroupLike]
            | relationship[Sequence[GroupLike]]
        ): ...
        @property
        def role(self) -> str | Column[str]: ...

else:
    _BaseRequest = object

_T = TypeVar('_T')
_F = TypeVar('_F', bound='Form')


@msgpack.make_serializable(tag=11)
class Message(NamedTuple):
    text: str
    type: MessageType


class ReturnToMixin(_BaseRequest):
    """ Provides a safe and convenient way of using return-to links.

    Return-to links are links with an added 'return-to' query parameter
    which points to the url a specific view (usually with a form) should
    return to, once all is said and done.

    There's no magic involved. If a view should honor the return-to
    paramter, it should use request.redirect instead of morepath.redirect.

    If no return-to parameter was specified, rqeuest.redirect is a
    transparent proxy to morepath.redirect.

    To create a link::

        url = request.return_to(original_url, redirect)

    To honor the paramter in a view, if present::

        return request.redirect(default_url)

    *Do not use the return-to parameter directly*. Redirect parameters
    are notorious for being used in phising attacks. By using ``return_to``
    and ``redirect`` you are kept safe from these attacks as the redirect
    url is signed and verified.

    For the same reason you should not allow the user-data for return-to
    links. Those are meant for internally generated links!

    """

    @property
    def identity_secret(self) -> str:
        raise NotImplementedError

    @property
    def redirect_signer(self) -> URLSafeSerializer:
        return URLSafeSerializer(self.identity_secret, 'return-to')

    @instance_lru_cache(maxsize=16)
    def sign_url_for_redirect(self, url: str) -> str:
        return self.redirect_signer.dumps(url)

    def return_to(self, url: str, redirect: str) -> str:
        signed = self.sign_url_for_redirect(redirect)
        return utils.append_query_param(url, 'return-to', signed)

    def return_here(self, url: str) -> str:
        return self.return_to(url, self.url)

    def redirect(self, url: str) -> Response:
        if 'return-to' in self.GET:
            try:
                url = self.redirect_signer.loads(self.GET['return-to'])
            except BadSignature:
                pass

        return morepath.redirect(url)


def is_logged_in(identity: Identity | NoIdentity) -> TypeGuard[Identity]:
    return identity is not NO_IDENTITY


class CoreRequest(IncludeRequest, ContentSecurityRequest, ReturnToMixin):
    """ Extends the default Morepath request with virtual host support and
    other useful methods.

    Virtual hosting might be supported by Morepath directly in the future:
    https://github.com/morepath/morepath/issues/185

    """

    app: Framework

    @cached_property
    def identity_secret(self) -> str:
        return self.app.identity_secret

    @cached_property
    def session(self) -> Session:
        return self.app.session()

    def link_prefix(
        self,
        app: Framework | None = None  # type:ignore[override]
    ) -> str:
        """ Override the `link_prefix` with the application base path provided
        by onegov.server, because the default link_prefix contains the
        hostname, which is not useful in our case - we'll add the hostname
        ourselves later.

        """
        return getattr(app or self.app, 'application_base_path', '')

    @cached_property
    def x_vhm_host(self) -> str:
        """ Return the X_VHM_HOST variable or an empty string.

        X_VHM_HOST acts like a prefix to all links generated by Morepath.
        If this variable is not empty, it will be added in front of all
        generated urls.
        """
        return self.headers.get('X_VHM_HOST', '').rstrip('/')

    @cached_property
    def x_vhm_root(self) -> str:
        """ Return the X_VHM_ROOT variable or an empty string.

        X_VHM_ROOT is a bit more tricky than X_VHM_HOST. It tells Morepath
        where the root of the application is situated. This means that the
        value of X_VHM_ROOT must be an existing path inside of Morepath.

        We can understand this best with an example. Let's say you have a
        Morepath application that serves a blog under /blog. You now want to
        serve the blog under a separate domain, say blog.example.org.

        If we just served Morepath under blog.example.org, we'd get urls like
        this one::

            blog.example.org/blog/posts/2014-11-17-16:00

        In effect, this subdomain would be no different from example.org
        (without the blog subdomain). However, we want the root of the host to
        point to /blog.

        To do this we set X_VHM_ROOT to /blog. Morepath will then automatically
        return urls like this::

            blog.example.org/posts/2014-11-17-16:00

        """
        return self.headers.get('X_VHM_ROOT', '').rstrip('/')

    @cached_property
    def path_url(self) -> str:
        """ Returns the path_url, taking the virtual hosting in account. """
        return self.transform(self.path)

    @cached_property
    def application_url(self) -> str:
        """ Extends the default application_url with virtual host suport. """
        # FIXME: Technically this is not guaranteed to be URL safe, but the
        #        same is already true for X_VHM_ROOT and X_VHM_HOST, if we
        #        want to be able to deal with this properly we should add
        #        a function that does the same thing webob does internally
        return self.transform(self.script_name).rstrip('/')

    def transform(self, url: str) -> str:
        """ Applies X_VHM_HOST and X_VHM_ROOT to the given url (which is
        expected to not contain a host yet!). """
        if self.x_vhm_root:
            url = '/' + url.removeprefix(self.x_vhm_root).lstrip('/')

        if self.x_vhm_host:
            url = self.x_vhm_host + url
        else:
            url = self.host_url + url

        return url

    @overload  # type:ignore[override]
    def link(
        self,
        obj: None,
        name: str = ...,
        default: None = ...,
        app: Framework | Sentinel = ...,
        query_params: SupportsItems[str, str] | None = ...,
        fragment: str | None = ...,
    ) -> None: ...

    @overload
    def link(
        self,
        obj: None,
        name: str,
        default: _T,
        app: Framework | Sentinel = ...,
        query_params: SupportsItems[str, str] | None = ...,
        fragment: str | None = ...,
    ) -> _T: ...

    @overload
    def link(
        self,
        obj: object,
        name: str = ...,
        default: Any = ...,
        app: Framework | Sentinel = ...,
        query_params: SupportsItems[str, str] | None = ...,
        fragment: str | None = ...,
    ) -> str: ...

    def link(
        self,
        obj: object,
        name: str = '',
        default: _T | None = None,
        app: Framework | Sentinel = SAME_APP,
        query_params: SupportsItems[str, str] | None = None,
        fragment: str | None = None,
    ) -> str | _T | None:
        """ Extends the default link generating function of Morepath. """
        query_params = query_params or {}
        if hasattr(obj, '__link_alias__'):
            result = obj.__link_alias__()
        else:
            result = self.transform(
                super().link(obj, name=name, default=default, app=app)
            )
        for key, value in query_params.items():
            result = append_query_param(result, key, value)
        if fragment:
            result += f'#{fragment}'
        return result

    def class_link(
        self,
        model: type[Any],
        variables: dict[str, Any] | None = None,
        name: str = '',
        app: Framework | Sentinel = SAME_APP,  # type:ignore[override]
    ) -> str:
        """ Extends the default class link generating function of Morepath. """
        return self.transform(super().class_link(
            model,
            variables=variables,
            name=name,
            app=app
        ))

    def filestorage_link(self, path: str) -> str | None:
        """ Takes the given filestorage path and returns an url if the path
        exists. The url might point to the local server or it might point to
        somehwere else on the web.

        """

        app = self.app
        if app.filestorage is None:
            return None

        if not app.filestorage.exists(path):
            return None

        if app.filestorage.hasurl(path):
            url = app.filestorage.geturl(path)

            if not url.startswith('file://'):
                return url

        return self.link(app.modules.filestorage.FilestorageFile(path))

    @cached_property
    def theme_link(self) -> str:
        """ Returns the link to the current theme. Computed once per request.

        The theme is automatically compiled and stored if it doesn't exist yet,
        or if it is outdated.

        """
        theme = self.app.settings.core.theme
        assert theme is not None, 'Do not call if no theme is used'

        force = self.app.always_compile_theme or (
            self.app.allow_shift_f5_compile
            and self.headers.get('cache-control') == 'no-cache'
            and self.headers.get('x-requested-with') != 'XMLHttpRequest')

        filename = self.app.modules.theme.compile(
            self.app.themestorage, theme, self.app.theme_options,
            force=force
        )

        return self.link(self.app.modules.theme.ThemeFile(filename))

    def get_session_nonce(self) -> str:
        """ Returns a nonce that can be passed as a POST parameter
        to restore a session in a context where the session cookie
        is unavailable, due to `SameSite=Lax`.
        """
        nonce = random_token()
        self.app.cache.set(
            nonce,
            self.app.sign(self.browser_session._token, nonce),
        )
        return self.app.sign(nonce)

    @cached_property
    def browser_session(self) -> BrowserSession:
        """ Returns a browser_session bound to the request. Works via cookies,
        so requests without cookies won't be able to use the browser_session.

        The browser session is bound to the application (by id), so no session
        data is shared between the applications.

        If no data is written to the browser_session, no session_id cookie
        is created.

        The session_id is rotated when users log in but not when they log out,
        that way we can still identify them and send messages when they log
        out.

        """

        if 'session_id' in self.cookies:
            session_id = self.app.unsign(self.cookies['session_id'])
            if session_id is None:
                # NOTE: this ensures the new session_id actually gets stored
                #       since on_dirty does nothing if the cookie exists
                #       otherwise we'll be stuck with an invalid session_id
                #       until we delete the cookie manually and will get
                #       infinite CSRF errors
                del self.cookies['session_id']
                session_id = random_token()

        elif isinstance(signed_nonce := self.POST.get('session_nonce'), str):
            nonce = self.app.unsign(signed_nonce)
            session_id = random_token()
            if nonce:
                # restore the session in a non SameSite context
                signed_session_id = self.app.cache.get(nonce)
                if signed_session_id:
                    # make sure this nonce can't be reused
                    self.app.cache.delete(nonce)
                    session_id = self.app.unsign(signed_session_id, nonce)
        else:
            session_id = random_token()

        def on_dirty(session: BrowserSession, token: str) -> None:

            if 'session_id' in self.cookies:
                return

            self.cookies['session_id'] = self.app.sign(token)

            @self.after
            def store_session(response: morepath.Response) -> None:
                response.set_cookie(
                    'session_id',
                    self.cookies['session_id'],
                    secure=self.app.identity_secure,
                    httponly=True,
                    samesite=self.app.same_site_cookie_policy  # type:ignore
                )

        return self.app.modules.browser_session.BrowserSession(
            cache=self.app.session_cache,
            token=session_id,
            on_dirty=on_dirty
        )

    def get_form(
        self,
        form_class: type[_F],
        i18n_support: bool = True,
        csrf_support: bool = True,
        data: dict[str, Any] | None = None,
        model: object = None,
        formdata: MultiDict[str, str | _FieldStorageWithFile] | None = None,
        pass_model: bool = False,
    ) -> _F:
        """ Returns an instance of the given form class, set up with the
        correct translator and with CSRF protection enabled (the latter
        doesn't work yet).

        Form classes passed to this function (or defined through the
        ``App.form`` directive) may define a ``on_request`` method, which
        is called after the request has been bound to the form and before
        the view function is called.

        """
        meta: dict[str, Any] = {}

        if i18n_support:
            translate = self.get_translate(for_chameleon=False)
            form_class = self.app.modules.i18n.get_translation_bound_form(
                form_class, translate)

            meta['locales'] = [self.locale, 'en'] if self.locale else []

        if csrf_support:
            meta['csrf'] = True
            meta['csrf_context'] = self.browser_session
            meta['csrf_class'] = SessionCSRF
            meta['csrf_secret'] = self.app.csrf_secret.encode('utf-8')
            meta['csrf_time_limit'] = timedelta(
                seconds=self.app.csrf_time_limit)

        # XXX it might be cleaner to always use the request in the meta,
        # instead of adding it to the form like it is done below - the meta
        # can also be accessed by form widgets
        meta['request'] = self
        meta['model'] = model

        # by default use POST data as formdata, but this can be overriden
        # by passing in something else as formdata
        if formdata is None and self.POST:
            formdata = self.POST
        form = form_class(
            formdata=formdata,
            meta=meta,
            data=data,
            obj=model if pass_model else None,
        )

        assert not hasattr(form, 'request')
        form.request = self  # type:ignore[attr-defined]
        form.model = model  # type:ignore[attr-defined]

        if hasattr(form, 'on_request'):
            form.on_request()

        return form

    @overload
    def translate(self, text: Markup | TranslationMarkup) -> Markup: ...
    @overload
    def translate(self, text: str) -> str: ...

    def translate(self, text: str) -> str:
        """ Translates the given text, if it's a translatable text. Also
        translates mappings. """

        if not hasattr(text, 'domain'):
            return text

        if (mapping := getattr(text, 'mapping', None)) is not None:
            for key, value in mapping.items():
                if hasattr(text, 'domain'):
                    mapping[key] = self.translator(value)

        return self.translator(text)

    @cached_property
    def translator(self) -> Callable[[str], str]:
        """ Returns the translate function for basic string translations. """
        translator = self.get_translate()

        def translate(text: str) -> str:
            if not hasattr(text, 'interpolate'):
                return text
            if translator:
                return text.interpolate(translator.gettext(text))
            return text.interpolate(text)

        return translate

    @cached_property
    def default_locale(self) -> str | None:
        """ Returns the default locale. """
        return self.app.default_locale

    @cached_property
    def locale(self) -> str | None:
        """ Returns the current locale of this request. """
        settings = self.app.settings

        locale = settings.i18n.locale_negotiator(self.app.locales, self)

        return locale or self.app.default_locale

    @cached_property
    def html_lang(self) -> str:
        """ The language code for the html tag. """
        return self.locale and self.locale.replace('_', '-') or ''

    @overload
    def get_translate(
        self,
        for_chameleon: Literal[False] = False
    ) -> GNUTranslations | None: ...

    @overload
    def get_translate(
        self,
        for_chameleon: Literal[True]
    ) -> _ChameleonTranslate | None: ...

    def get_translate(
        self,
        for_chameleon: bool = False
    ) -> GNUTranslations | _ChameleonTranslate | None:
        """ Returns the translate method to the given request, or None
        if no such method is availabe.

        :for_chameleon:
            True if the translate instance is used for chameleon (which is
            special).

        """

        if not self.app.locales:
            return None

        locale = self.locale
        if locale is None:
            return None

        if for_chameleon:
            return self.app.chameleon_translations.get(locale)
        else:
            return self.app.translations.get(locale)

    def message(self, text: str, type: MessageType) -> None:
        """ Adds a message with the given type to the messages list. This
        messages list may then be displayed by an application building on
        onegov.core.

        For example::

            http://foundation.zurb.com/docs/components/alert_boxes.html

        Four default types are defined on the request for easier use:

        :meth:`success`
        :meth:`warning`
        :meth:`info`
        :meth:`alert`

        The messages are stored with the session and to display them, the
        template using the messages should call :meth:`consume_messages`.

        """
        if not self.browser_session.has('messages'):
            self.browser_session.messages = [Message(text, type)]
        else:
            # this is a bit akward, but I don't see an easy way for this atm.
            # (otoh, usually there's going to be one message only)
            self.browser_session.messages = [
                *self.browser_session.messages,
                Message(text, type)
            ]

    def consume_messages(self) -> Iterator[Message]:
        """ Returns the messages, removing them from the session in the
        process. Call only if you can be reasonably sure that the user
        will see the messages.

        """
        yield from self.browser_session.pop('messages', ())

    def success(self, text: str) -> None:
        """ Adds a success message. """
        self.message(text, 'success')

    def warning(self, text: str) -> None:
        """ Adds a warning message. """
        self.message(text, 'warning')

    def info(self, text: str) -> None:
        """ Adds an info message. """
        self.message(text, 'info')

    def alert(self, text: str) -> None:
        """ Adds an alert message. """
        self.message(text, 'alert')

    @cached_property
    def is_logged_in(self) -> bool:
        """ Returns True if the current request is logged in at all. """
        return self.identity is not NO_IDENTITY

    @cached_property
    def agent(self) -> ua_parser.DefaultedResult:
        """ Returns the user agent, parsed by ua-parser. """
        return ua_parser.parse(self.user_agent or '').with_defaults()

    def has_permission(
        self,
        model: object,
        permission: type[Intent] | None,
        user: UserLike | None = None
    ) -> bool:
        """ Returns True if the current or given user has the given permission
        on the given model.

        """
        if permission is None:
            return True

        identity = self.app.application_bound_identity(
            user.username,
            user.id.hex,
            frozenset(group.id.hex for group in user.groups),
            user.role
        ) if user else self.identity

        return self.app._permits(identity, model, permission)

    def has_access_to_url(self, url: str) -> bool:
        """ Returns true if the current user has access to the given url.

        The domain part of the url is completely ignored. This method should
        only be used if you have no other choice. Loading the object by
        url first is slower than if you can get the object otherwise.

        The initial use-case for this function is the to parameter in the
        login view. If the to-url is accessible anyway, we skip the login
        view.

        If we can't find a view for the url, a KeyError is thrown.

        """
        obj, view_name = self.app.object_by_path(url, with_view_name=True)

        if obj is None:
            raise KeyError("Could not find view for '{}'".format(url))

        permission = self.app.permission_by_view(obj, view_name)
        return self.has_permission(obj, permission)

    def exclude_invisible(self, models: Iterable[_T]) -> list[_T]:
        """ Excludes models invisble to the current user from the list. """
        return [m for m in models if self.is_visible(m)]

    def is_visible(self, model: object) -> bool:
        """ Returns True if the given model is visible to the current user.

        In addition to the `is_public` check, this checks if the model is
        secret and should therefore not be visible (though it can still be
        reached via URL).

        """

        if not self.is_public(model):
            return False

        if not self.is_private(model) and hasattr(model, 'access'):
            if model.access in ('secret', 'secret_mtan'):
                return False

        return True

    def is_public(self, model: object) -> bool:
        """ Returns True if the current user has the Public permission for
        the given model.

        """
        return self.has_permission(model, self.app.modules.security.Public)

    def is_personal(self, model: object) -> bool:
        """ Returns True if the current user has the Personal permission for
        the given model.

        """
        return self.has_permission(model, self.app.modules.security.Personal)

    def is_private(self, model: object) -> bool:
        """ Returns True if the current user has the Private permission for
        the given model.

        """
        return self.has_permission(model, self.app.modules.security.Private)

    def is_secret(self, model: object) -> bool:
        """ Returns True if the current user has the Secret permission for
        the given model.

        """
        return self.has_permission(model, self.app.modules.security.Secret)

    @cached_property
    def current_role(self) -> str | None:
        """ Returns the user-role of the current request, if logged in.
        Otherwise, None is returned.

        """
        return self.identity.role if is_logged_in(self.identity) else None

    def has_role(self, *roles: str) -> bool:
        """ Returns true if the current user has any of the given roles. """

        assert roles and all(roles)
        return self.current_role in roles

    @cached_property
    def csrf_salt(self) -> str:
        if not self.browser_session.has('csrf_salt'):
            self.browser_session['csrf_salt'] = random_token()

        return self.browser_session['csrf_salt']

    def new_csrf_token(self, salt: str | bytes | None = None) -> bytes:
        """ Returns a new CSRF token. A CSRF token can be verified
        using :meth:`is_valid_csrf_token`.

        Note that forms do their own CSRF protection. This is meant
        for CSRF protection outside of forms.

        onegov.core uses the Synchronizer Token Pattern for CSRF protection:
        `<https://www.owasp.org/index.php/\
        Cross-Site_Request_Forgery_%28CSRF%29_Prevention_Cheat_Sheet>`_

        New CSRF tokens are signed usign a secret attached to the session (but
        not sent out to the user). Clients have to return the CSRF token they
        are given. The token has to match the secret, which the client doesn't
        know. So an attacker would have to get access to both the cookie and
        the html source to be able to forge a request.

        Since cookies are marked as HTTP only (no javascript access), this
        even prevents CSRF attack combined with XSS.

        """
        assert salt or self.csrf_salt
        salt = salt or self.csrf_salt

        # use app.identity_secret here, because that's being used for
        # more.itsdangerous, which uses the same algorithm
        signer = TimestampSigner(self.identity_secret, salt=salt)

        return signer.sign(random_token())

    @cached_property
    def csrf_token(self) -> str:
        """ Returns a csrf token for use with DELETE links (forms do their
        own thing automatically).

        """
        return self.new_csrf_token().decode('utf-8')

    def csrf_protected_url(self, url: str) -> str:
        """ Adds a csrf token to the given url. """
        return utils.append_query_param(url, 'csrf-token', self.csrf_token)

    def assert_valid_csrf_token(
        self,
        signed_value: str | bytes | None = None,
        salt: str | bytes | None = None
    ) -> None:
        """ Validates the given CSRF token and returns if it was
        created by :meth:`new_csrf_token`. If there's a mismatch, a 403 is
        raised.

        If no signed_value is passed, it is taken from
        request.params.get('csrf-token').

        """
        _signed_value = signed_value or self.params.get('csrf-token')
        salt = salt or self.csrf_salt
        if not _signed_value:
            raise HTTPForbidden()

        # params on request could contain a cgi.FieldStorage, so lets make
        # sure we are dealing with str or bytes
        if not isinstance(_signed_value, (str, bytes)):
            raise HTTPForbidden()

        if not salt:
            raise HTTPForbidden()

        signer = TimestampSigner(self.identity_secret, salt=salt)
        try:
            signer.unsign(_signed_value, max_age=self.app.csrf_time_limit)
        except (SignatureExpired, BadSignature) as exception:
            raise HTTPForbidden() from exception

    def new_url_safe_token(
        self,
        data: object,
        salt: str | bytes | None = None
    ) -> str:
        """ Returns a new URL safe token. A token can be deserialized
        using :meth:`load_url_safe_token`.

        """
        serializer = URLSafeTimedSerializer(self.identity_secret)
        return serializer.dumps(data, salt=salt)

    def load_url_safe_token(
        self,
        data: str | bytes | None,
        salt: str | bytes | None = None,
        max_age: int | None = 3600
    ) -> Any | None:
        """ Deserialize a token created by :meth:`new_url_safe_token`.

        If the token is invalid, None is returned.

        """
        if not data:
            return None
        serializer = URLSafeTimedSerializer(self.identity_secret)
        try:
            return serializer.loads(data, salt=salt, max_age=max_age)
        except (SignatureExpired, BadSignature):
            return None

    @cached_property
    def template_loader(self) -> TemplateLoader:
        """ Returns the chameleon template loader. """
        registry = self.app.config.template_engine_registry
        return registry._template_loaders['.pt']

    @property
    def analytics_provider(self) -> AnalyticsProvider | None:
        """ Returns the active analytics provider. """
        return None

    @property
    def analytics_code(self) -> Markup | None:
        """ Return the embeddable code for the active analytics provider. """
        provider = self.analytics_provider
        if provider is None:
            return None

        return provider.code(self)

    def require_unsafe_eval(self) -> None:
        # FIXME: We currently use some intercooler features in some views
        #        that require unsafe-eval, we should try to get rid of them
        #        by writing some custom JavaScript handlers (ic-on-XXX).
        self.content_security_policy.script_src.add(UNSAFE_EVAL)

    # NOTE: We override this so we pass an instance of ourselves
    #       to resolve_model, rather than a base Request instance
    #       like in the original implementation, the original
    #       implementation also doesn't handle query params
    #       correctly, which can lead to converter errors
    def resolve_path(
        self,
        path: str,
        app: App | Sentinel = SAME_APP
    ) -> Any | None:
        """Resolve a path to a model instance.

        The resulting object is a model instance, or ``None`` if the
        path could not be resolved.

        :param path: URL path to resolve.
        :param app: If set, change the application in which the
          path is resolved. By default the path is resolved in the
          current application.
        :return: instance or ``None`` if no path could be resolved.
        """
        if app is None:
            raise LinkError('Cannot path: app is None')

        if app is SAME_APP:
            app = self.app

        path_info, __, query_string = path.partition('?')

        environ = self.environ.copy()
        environ.pop('webob._parsed_post_vars', None)
        request = self.__class__(
            environ,
            cast('App', app),
            method='GET',
            path_info=path_info,
            query_string=query_string,
            body=b''
        )
        # try to resolve imports..
        from morepath.publish import resolve_model

        return resolve_model(request)
