from __future__ import annotations

import calendar
import time

from abc import ABCMeta, abstractmethod
from uuid import uuid4

import morepath
from attr import attrs, attrib, validators
from jwt.exceptions import InvalidTokenError, PyJWKClientError
from oauthlib.oauth2 import OAuth2Error
from sedate import utcnow

from onegov.core.crypto import random_token
from onegov.user import _, log, UserCollection
from onegov.user.auth.clients import KerberosClient
from onegov.user.auth.clients import LDAPClient
from onegov.user.auth.clients.oidc import OIDCConnections
from onegov.user.auth.clients.msal import MSALConnections
from onegov.user.auth.clients.saml2 import SAML2Connections
from onegov.user.auth.clients.saml2 import finish_logout
from saml2.ident import code
from webob import Response


from typing import Any, ClassVar, Literal, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Mapping
    from onegov.core.request import CoreRequest
    from onegov.user import User, UserApp
    from sqlalchemy.orm import Session
    from translationstring import TranslationString
    from typing import Protocol

    class HasName(Protocol):
        @property
        def name(self) -> str: ...

    class HasApplicationIdAndNamespace(Protocol):
        @property
        def application_id(self) -> str: ...
        @property
        def namespace(self) -> str: ...


AUTHENTICATION_PROVIDERS = {}


class Conclusion:
    """ A final answer of :meth:`AuthenticationProvider`. """


@attrs(slots=True, frozen=True)
class Success(Conclusion):
    """ Indicates a sucessful authentication. """

    user: User = attrib()
    note: TranslationString = attrib()

    def __bool__(self) -> Literal[True]:
        return True


@attrs(slots=True, frozen=True)
class Failure(Conclusion):
    """ Indicates a corrupt JWT """

    note: TranslationString = attrib()

    def __bool__(self) -> Literal[False]:
        return False


class InvalidJWT(Failure):
    """ Indicates a failed authentication. """

    note: TranslationString = attrib()

    def __bool__(self) -> Literal[False]:
        return False


@attrs(slots=True, frozen=True)
class ProviderMetadata:
    """ Holds provider-specific metadata. """

    name: str = attrib()
    title: str = attrib()


@attrs()
class AuthenticationProvider(metaclass=ABCMeta):
    """ Base class and registry for third party authentication providers. """

    # stores the 'to' attribute for the integration app
    # :class:`~onegov.user.integration.UserApp`.
    to: str | None = attrib(init=False)
    primary: bool = attrib(init=False, default=False)
    name: str = attrib()

    if TYPE_CHECKING:
        # forward declare for type checking
        metadata: ClassVar[HasName]
        kind: ClassVar[Literal['separate', 'integrated']]

    def __init_subclass__(
        cls,
        metadata: HasName | None = None,
        **kwargs: Any
    ):
        if metadata:
            global AUTHENTICATION_PROVIDERS
            assert metadata.name not in AUTHENTICATION_PROVIDERS

            # reserved names
            assert metadata.name != 'auto'

            cls.metadata = metadata
            AUTHENTICATION_PROVIDERS[metadata.name] = cls

        else:
            assert cls.kind in ('separate', 'integrated')

        super().__init_subclass__(**kwargs)

    @classmethod
    @abstractmethod
    def configure(cls, name: str, **kwargs: Any) -> Self | None:
        """ This function gets called with the per-provider configuration
        defined in onegov.yml. Authentication providers may optionally
        access these values.

        The return value is either a provider instance, or none if the
        provider is not available.

        """

        return cls(name=name)

    def is_primary(self, app: UserApp) -> bool:
        """ Returns whether the authentication provider is intended to be
        the primary provider for this app."""
        return self.primary if self.available(app) else False

    def available(self, app: UserApp) -> bool:
        """Returns whether the authentication provider is available for the
        current app. Since there are tenant specific connections, we want to
        tcheck, if for the tenant of the app, there is an available client."""
        return True


@attrs()
class SeparateAuthenticationProvider(AuthenticationProvider):
    """ Base class for separate authentication providers.

    Seperate providers render a button which the user can click to do a
    completely separate request/response handling that eventually should lead
    to an authenticated user.

    """

    kind: ClassVar[Literal['separate']] = 'separate'

    @abstractmethod
    def authenticate_request(
        self,
        request: CoreRequest
    ) -> Success | Failure | Response | None:
        """ Authenticates the given request in one or many steps.

        Providers are expected to return one of the following values:

        * A conclusion (if the authentication was either successful or failed)
        * None (if the authentication failed)
        * A webob response (to perform handshakes)

        This function is called whenever the authentication is initiated by
        the user. If the provider returns a webob response, it is returned
        as is by the calling view.

        Therefore, `authenticate_request` must take care to return responses
        in a way that eventually end up fulfilling the authentication. At the
        very least, providers should ensure that all parameters of the original
        request are kept when asking external services to call back.

        """

    @abstractmethod
    def button_text(self, request: CoreRequest) -> str:
        """ Returns the translatable button text for the given request.

        It is okay to return a static text, if the button remains the same
        for all requests.

        The translatable text is parsed as markdown, to add weight to
        the central element of the text. For example::

            Login with **Windows**

        """


@attrs()
class IntegratedAuthenticationProvider(AuthenticationProvider):
    """ Base class for integrated authentication providers.

    Integrated providers use the username/password entered in the normal
    login form and perform authentication that way (with fallback to the
    default login mechanism).

    """

    kind: ClassVar[Literal['integrated']] = 'integrated'

    @abstractmethod
    def hint(self, request: CoreRequest) -> str:
        """ Returns the translatable hint shown above the login mask for
        the integrated provider.

        It is okay to return a static text, if the hint remains the same
        for all requests.

        The translatable text is parsed as markdown.

        """

    @abstractmethod
    def authenticate_user(
        self,
        request: CoreRequest,
        username: str,
        password: str
    ) -> User | None:
        """ Authenticates the given username/password in a single step.

        The function is expected to return an existing user record or None.

        """


def spawn_ldap_client(
    ldap_url: str | None = None,
    ldap_username: str | None = None,
    ldap_password: str | None = None,
    **cfg: Any
) -> LDAPClient:
    """ Takes an LDAP configuration as found in the YAML and spawns an LDAP
    client that is connected. If the connection fails, an exception is raised.

    """
    # FIXME: the defaults should probably pass type checking, we just need
    #        to make sure try_configuration still raises an Exception
    client = LDAPClient(
        url=ldap_url,  # type:ignore[arg-type]
        username=ldap_username,  # type:ignore[arg-type]
        password=ldap_password)  # type:ignore[arg-type]

    try:
        client.try_configuration()
    except Exception as exception:
        raise ValueError(f'LDAP config error: {exception}') from exception

    return client


def ensure_user(
    source: str | None,
    source_id: str | None,
    session: Session,
    username: str,
    role: str,
    force_role: bool = True,
    realname: str | None = None,
    force_active: bool = False
) -> User:
    """ Creates the given user if it doesn't already exist. Ensures the
    role is set to the given role in all cases.
    """

    users = UserCollection(session)

    # find the user by source
    if source and source_id:
        user = users.by_source_id(source, source_id)
    else:
        user = None

    # fall back to the username
    user = user or users.by_username(username)

    if not user:
        log.info(f'Adding user {username} from {source}:{source_id}')
        user = users.add(
            username=username,
            password=random_token(),
            role=role
        )
    elif force_active and not user.active:
        user.active = True

    # update the username
    if user.username != username:
        # ensure the new username is available
        if users.by_username(username) is not None:
            log.error(f'Cannot rename user {user.username} to {username}')
        else:
            user.username = username

    # update the role even if the user exists already
    if force_role:
        user.role = role

    # the source of the user is always the last provider that was used
    user.source = source
    user.source_id = source_id
    user.realname = realname

    return user


@attrs(auto_attribs=True)
class RolesMapping:
    """ Takes a role mapping and provides access to it.

    A role mapping maps a onegov-cloud role to an LDAP role. For example:

        admins -> ACC_OneGovCloud_User

    The mapping comes in multiple
    levels. For example:

       * "__default__"         Fallback for all applications
       * "onegov_org"          Namespace specific config
       * "onegov_org/govikon"  Application specific config

    Each level contains a group name for admins, editors and members.
    See onegov.yml.example for an illustrated example.

    """

    roles: dict[str, dict[str, str]]

    def app_specific(
        self,
        app: HasApplicationIdAndNamespace
    ) -> dict[str, str] | None:

        if app.application_id in self.roles:
            return self.roles[app.application_id]

        if app.namespace in self.roles:
            return self.roles[app.namespace]

        # FIXME: This should probably be self.roles['__default__'] since
        #        match doesn't work with None
        return self.roles.get('__default__')

    def match(
        self,
        roles: Mapping[str, str],
        groups: Collection[str]
    ) -> str | None:
        """ Takes a role mapping (the fallback, namespace, or app specific one)
        and matches it against the given LDAP groups.

        Returns the matched group or None.

        """
        groups = {g.lower() for g in groups}

        for role in ('admin', 'editor', 'supporter', 'member'):
            if (
                (group := roles.get(f'{role}s', None)) is not None
                and group.lower() in groups
            ):
                return role

        return None


@attrs(auto_attribs=True)
class LDAPAttributes:
    """ Holds the LDAP server-specific attributes. """

    # the name of the Distinguished Name (DN) attribute
    name: str

    # the name of the e-mails attribute (returns a list of emails)
    mails: str

    # the name of the group membership attribute (returns a list of groups)
    groups: str

    # the name of the password attribute
    password: str

    # the name of the uid attribute
    uid: str

    @classmethod
    def from_cfg(cls, cfg: dict[str, Any]) -> Self:
        return cls(
            name=cfg.get('name_attribute', 'cn'),
            mails=cfg.get('mails_attribute', 'mail'),
            groups=cfg.get('groups_attribute', 'memberOf'),
            password=cfg.get('password_attribute', 'userPassword'),
            uid=cfg.get('uid_attribute', 'uid'),
        )


@attrs(auto_attribs=True)
class LDAPProvider(
        IntegratedAuthenticationProvider, metadata=ProviderMetadata(
            name='ldap', title=_('LDAP'))):

    """ Generic LDAP Provider that includes authentication via LDAP. """

    # The LDAP client to use
    ldap: LDAPClient = attrib()

    # The authentication method to use
    #
    #   * bind =>    The authentication is made by rebinding the connection
    #                to the LDAP server. This is the more typical approach, but
    #                also slower. It requires that users that can authenticate
    #                may also create a connection to the LDAP server.
    #
    #                (not yet implemented)
    #
    #   * compare => Uses the existing LDAP client connection and checks the
    #                given password using the LDAP COMPARE operation. Since
    #                this is the first approach we implemented, it is the
    #                default.
    #
    auth_method: str = attrib(
        validator=validators.in_(
            ('bind', 'compare')
        )
    )

    # The LDAP attributes configuration
    attributes: LDAPAttributes = attrib()

    # Roles configuration
    roles: RolesMapping = attrib()

    # Custom hint to be shown in the login view
    custom_hint: str = ''

    @classmethod
    def configure(cls, name: str, **cfg: Any) -> Self | None:

        # Providers have to decide themselves if they spawn or not
        if not cfg:
            return None

        # LDAP configuration
        ldap = spawn_ldap_client(**cfg)

        return cls(
            name=name,
            ldap=ldap,
            auth_method=cfg.get('auth_method', 'compare'),
            attributes=LDAPAttributes.from_cfg(cfg),
            custom_hint=cfg.get('hint', ''),
            roles=RolesMapping(cfg.get('roles', {
                '__default__': {
                    'admins': 'admins',
                    'editors': 'editors',
                    'supporters': 'supporters',
                    'members': 'members',
                }
            })),
        )

    def hint(self, request: CoreRequest) -> str:
        return self.custom_hint

    def authenticate_user(
        self,
        request: CoreRequest,
        username: str,
        password: str
    ) -> User | None:

        if self.auth_method == 'compare':
            return self.authenticate_using_compare(request, username, password)

        raise NotImplementedError()

    def authenticate_using_compare(
        self,
        request: CoreRequest,
        username: str,
        password: str
    ) -> User | None:

        # since this is turned into an LDAP query, we want to make sure this
        # is not used to make broad queries
        assert '*' not in username
        assert '&' not in username
        assert '?' not in username

        # onegov-cloud uses the e-mail as username, therefore we need to query
        # LDAP to get the designated name (actual LDAP username)
        query = f'({self.attributes.mails}={username})'
        query_attrs = (
            self.attributes.groups,
            self.attributes.mails,
            self.attributes.uid
        )

        # we query the groups at the same time, so if we have a password
        # match we are all ready to go
        entries = self.ldap.search(query, query_attrs)

        # as a fall back, we try to query the uid
        if not entries:
            query = f'({self.attributes.uid}={username})'
            entries = self.ldap.search(query, query_attrs)

            # if successful we need the e-mail address
            for name, _attrs in (entries or {}).items():
                try:
                    username = _attrs[self.attributes.mails][0]
                except IndexError:
                    log.warning(
                        f'Email missing in LDAP for user with uid {username}')
                    return None
                break

        # then, we give up
        if not entries:
            log.warning(f'No LDAP user with uid ore-mail {username}')
            return None

        if len(entries) > 1:
            log.warning(f'Found more than one user for e-mail {username}')
            log.warning('All but the first user will be ignored')

        for name, _attrs in entries.items():
            groups = _attrs[self.attributes.groups]
            uid = _attrs[self.attributes.uid][0]

            # do not iterate over all entries, or this becomes a very
            # handy way to check a single password against multiple
            # (or possibly all) entries!
            break

        # We might talk to a very fast LDAP server which an attacker could use
        # to brute force passwords. We already throttle this on the server, but
        # additional measures never hurt.
        time.sleep(0.25)

        if not self.ldap.compare(name, self.attributes.password, password):
            log.warning(f'Wrong password for {username} ({name})')
            return None

        # finally check if we have a matching role
        roles = self.roles.app_specific(request.app)
        # NOTE: If we don't get a roles mapping at all, that is a configuration
        #       error, so it's fine if roles.match throws an exception, it
        #       might be better to raise in roles.app_specific though, but
        #       then again we also expect a certain format, we should maybe
        #       consider making our configuration a pydantic model, so the
        #       global/app specific config is verified at startup
        role = self.roles.match(roles, groups)  # type:ignore[arg-type]

        if not role:
            log.warning(f'Wrong role for {username} ({name})')
            return None

        return ensure_user(
            source=self.name,
            source_id=uid,
            session=request.session,
            username=username,
            role=role)


@attrs(auto_attribs=True)
class LDAPKerberosProvider(
        SeparateAuthenticationProvider, metadata=ProviderMetadata(
            name='ldap_kerberos', title=_('LDAP Kerberos'))):

    """ Combines LDAP with Kerberos. LDAP handles authorisation, Kerberos
    handles authentication.

    """

    # The LDAP client to use
    ldap: LDAPClient = attrib()

    # The Kerberos client to use
    kerberos: KerberosClient = attrib()

    # LDAP attributes configuration
    attributes: LDAPAttributes = attrib()

    # Roles configuration
    roles: RolesMapping = attrib()

    # Optional suffix that is removed from the Kerberos username if present
    suffix: str | None = None

    @classmethod
    def configure(cls, name: str, **cfg: Any) -> Self | None:

        # Providers have to decide themselves if they spawn or not
        if not cfg:
            return None

        # LDAP configuration
        ldap = spawn_ldap_client(**cfg)

        # Kerberos configuration
        kerberos = KerberosClient(
            keytab=cfg.get('kerberos_keytab', None),  # type: ignore[arg-type]
            hostname=cfg.get('kerberos_hostname', None),  # type: ignore[arg-type]
            service=cfg.get('kerberos_service', None))  # type: ignore[arg-type]

        provider = cls(
            name=name,
            ldap=ldap,
            kerberos=kerberos,
            attributes=LDAPAttributes.from_cfg(cfg),
            suffix=cfg.get('suffix', None),
            roles=RolesMapping(cfg.get('roles', {
                '__default__': {
                    'admins': 'admins',
                    'editors': 'editors',
                    'supporters': 'supporters',
                    'members': 'members',
                }
            }))
        )
        if cfg.get('primary', False):
            provider.primary = True
        return provider

    def button_text(self, request: CoreRequest) -> str:
        """ Returns the request tailored to each OS (users won't understand
        LDAP/Kerberos, but for them it's basically their local OS login).

        """
        user_os = request.agent.os.family

        if user_os == 'Other':
            return _('Login with operating system')

        return _('Login with **${operating_system}**', mapping={
            'operating_system': user_os
        })

    def authenticate_request(
        self,
        request: CoreRequest
    ) -> Response | Success | Failure:

        response = self.kerberos.authenticated_username(request)

        # handshake
        if isinstance(response, Response):
            return response

        # authentication failed
        if response is None:
            return Failure(_('Authentication failed'))

        # we got authentication, do we also have authorization?
        name = response
        user = self.request_authorization(request=request, username=name)

        if user is None:
            return Failure(_('User «${user}» is not authorized', mapping={
                'user': name
            }))

        return Success(user, _('Successfully logged in as «${user}»', mapping={
            'user': user.username
        }))

    def request_authorization(
        self,
        request: CoreRequest,
        username: str
    ) -> User | None:

        if self.suffix:
            username = username.removesuffix(self.suffix)

        entries = self.ldap.search(
            query=f'({self.attributes.name}={username})',
            attributes=[self.attributes.mails, self.attributes.groups])

        if not entries:
            log.warning(f'No LDAP entries for {username}')
            return None

        if len(entries) > 1:
            tip = ', '.join(entries.keys())
            log.warning(f'Multiple LDAP entries for {username}: {tip}')
            return None

        attributes = next(v for v in entries.values())

        mails = attributes[self.attributes.mails]
        if not mails:
            log.warning(f'No e-mail addresses for {username}')
            return None

        groups = attributes[self.attributes.groups]
        if not groups:
            log.warning(f'No groups for {username}')
            return None

        # get the common name of the groups
        groups = {g.lower().split(',')[0].split('cn=')[-1] for g in groups}

        # get the roles
        roles = self.roles.app_specific(request.app)

        if not roles:
            log.warning(f'No role map for {request.app.application_id}')
            return None

        role = self.roles.match(roles, groups)
        if not role:
            log.warning(f'No authorized group for {username}')
            return None

        return ensure_user(
            source=self.name,
            source_id=username,
            session=request.session,
            username=mails[0],
            role=role)


@attrs
class OauthProvider(SeparateAuthenticationProvider):
    """General Prototype class for an Oath Provider with typical OAuth flow.
    """

    @abstractmethod
    def do_logout(
        self,
        request: CoreRequest,
        user: User,
        to: str
    ) -> Response | None:
        """ May return a webob response that gets used instead of the default
        logout response, to perform e.g. a redirect to the external provider.

        If no special response is necessary because the external logout is
        skipped/unecessary or performed through a back-channel, this will
        just return None and fall through to the default logout response
        which will terminate the local user session.
        """

    @abstractmethod
    def request_authorisation(
        self,
        request: CoreRequest
    ) -> Success | Failure | Response:
        """
        Takes the request from the redirect_uri view sent from the users
        browser. The redirect view expects either:
        * a Conclusion, either Success or Failure
        * a webob response, e.g. to redirect to the logout page

        The redirect view, where this function is used, will eventually fulfill
        the login process whereas :func:`self.authenticate_request` is purely
        to redirect the user to the auth provider.
        """

    def logout_redirect_uri(self, request: CoreRequest) -> str:
        """This url usually has to be registered with the OAuth Provider.
        Should not contain any query parameters. """
        return request.class_link(
            AuthenticationProvider,
            {'name': self.name},
            name='logout'
        )

    def redirect_uri(self, request: CoreRequest) -> str:
        """Returns the redirect uri in a consistent manner
        without query parameters."""
        return request.class_link(
            AuthenticationProvider,
            {'name': self.name},
            name='redirect'
        )


@attrs(auto_attribs=True)
class AzureADProvider(
    OauthProvider,
    metadata=ProviderMetadata(name='msal', title=_('AzureAD'))
):
    """
    Authenticates and authorizes a user in AzureAD for a specific AzureAD
    tenant_id and client_id in an OpenID Connect flow.

    For this to work, we need

        - Client ID
        - Client Secret
        - Tenant ID

    We have to give the AzureAD manager following Urls, that should not change:

        - Redirect uri (https://<host>/auth_providers/msal/redirect)
        - Logout Redirect uri (https://<host>/auth/logout)

    Additionally, weh AzureAD Manager should set additional token claims
    for the authorisation to work:

        - `email` claim
        - `groups` claim for role mapping
        - optional: `family_name` and `given_name` for User.realname

    The claims `preferred_username` or `upn` could also be used for
    User.realname."""

    # msal instances by tenant
    tenants: MSALConnections = attrib()

    # Roles configuration
    roles: RolesMapping = attrib()

    # Custom hint to be shown in the login view
    custom_hint: str = ''

    @classmethod
    def configure(cls, name: str, **cfg: Any) -> Self | None:

        if not cfg:
            return None

        return cls(
            name=name,
            tenants=MSALConnections.from_cfg(cfg.get('tenants', {})),
            custom_hint=cfg.get('hint', ''),
            roles=RolesMapping(cfg.get('roles', {
                '__default__': {
                    'admins': 'admins',
                    'editors': 'editors',
                    'supporters': 'supporters',
                    'members': 'members'
                }
            }))
        )

    def button_text(self, request: CoreRequest) -> str:
        return _('Login with Microsoft')

    def do_logout(self, request: CoreRequest, user: User, to: str) -> None:
        # global logout is deactivated for AzureAD currently
        return None

    def logout_url(self, request: CoreRequest) -> str:
        client = self.tenants.client(request.app)
        assert client is not None
        return client.logout_url(self.logout_redirect_uri(request))

    def authenticate_request(
        self,
        request: CoreRequest
    ) -> Response | Failure:
        """
        Returns a redirect response or a Conclusion

        Parameters of the original request are kept for when external services
        call back.
        """

        app = request.app
        client = self.tenants.client(app)
        roles = self.roles.app_specific(app)

        if not roles:
            # Considered as a misconfiguration of the app
            log.error(f'No role map for {app.application_id}')
            return Failure(_('Authorisation failed due to an error'))

        if not client:
            # Considered as a misconfiguration of the app
            log.error(f'No msal client found for '
                      f'{app.application_id} or {app.namespace}')
            return Failure(_('Authorisation failed due to an error'))

        state = app.sign(str(uuid4()), 'azure-ad')
        nonce = str(uuid4())
        request.browser_session['state'] = state
        request.browser_session['login_to'] = self.to
        request.browser_session['nonce'] = nonce

        # We can not include self.to, the redirect uri must always be the same
        auth_url = client.connection.get_authorization_request_url(
            scopes=[],
            state=state,
            redirect_uri=self.redirect_uri(request),
            response_type='code',
            nonce=nonce
        )

        return morepath.redirect(auth_url)

    def validate_id_token(
        self,
        request: CoreRequest,
        token: dict[str, Any]
    ) -> Failure | Literal[True]:
        """
        Makes sure the id token is validated correctly according to
        https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation
        """

        app = request.app
        client = self.tenants.client(app)
        id_token_claims = token.get('id_token_claims', {})
        iss = id_token_claims.get('iss')

        assert client is not None
        endpoint = client.connection.authority.token_endpoint
        endpoint = endpoint.replace('oauth2/', '').replace('token', '')
        endpoint = endpoint.rstrip('/')

        if iss != endpoint:
            log.info(f'Issue claim check failed: {iss} v.s {endpoint}')
            return Failure(_('Authorisation failed due to an error'))

        now = utcnow().timestamp()
        iat = id_token_claims.get('iat')
        if iat > now:
            log.info(f'IAT check failed: {iat} > {now}')
            return Failure(_('Authorisation failed due to an error'))
        exp = id_token_claims.get('exp')
        if now > exp:
            log.info(f'EXP check failed, token expired: {now} > {exp}')
            return Failure(_('Your login has expired'))

        return True

    def request_authorisation(
        self,
        request: CoreRequest
    ) -> Success | Failure:
        """
        If "Stay Logged In" on the Microsoft Login page is chosen,
        AzureAD behaves like an auto-login provider, redirecting the user back
        immediately to the redirect view without prompting a password or
        even showing any Microsoft page. Microsoft set their own cookies to
        make this possible.

        Return a webob Response or a Conclusion.
        """
        # Fetch the state that was saved upon first redirect
        app = request.app
        state = request.browser_session.get('state')

        client = self.tenants.client(app)
        assert client is not None
        roles = self.roles.app_specific(app)

        if request.params.get('state') != state:
            log.warning('state is not matching, csrf check failed')
            return Failure(_('Authorisation failed due to an error'))

        authorization_code = request.params.get('code')

        if not isinstance(authorization_code, str):
            log.warning('No code found in url query params')
            return Failure(_('Authorisation failed due to an error'))

        # Must take the same redirect url as used in the first step
        # The nonce is evaluated inside msal library and raises ValueError
        token_result = client.connection.acquire_token_by_authorization_code(
            authorization_code,
            scopes=[],
            redirect_uri=self.redirect_uri(request),
            nonce=request.browser_session.pop('nonce')
        )

        if 'error' in token_result:
            log.info(
                f"Error in token result - "
                f"{token_result['error']}: "
                f"{token_result.get('error_description')}"
            )
            return Failure(_('Authorisation failed due to an error'))

        validate_conclusion = self.validate_id_token(request, token_result)
        if not validate_conclusion:
            return validate_conclusion

        id_token_claims = token_result.get('id_token_claims', {})
        username = id_token_claims.get(client.attributes.username)
        source_id = id_token_claims.get(client.attributes.source_id)
        groups = id_token_claims.get(client.attributes.groups)
        first_name = id_token_claims.get(client.attributes.first_name)
        last_name = id_token_claims.get(client.attributes.last_name)
        preferred_username = id_token_claims.get(
            client.attributes.preferred_username)

        if not username:
            log.info('No username found in authorisation step')
            return Failure(_('Authorisation failed due to an error'))

        if not source_id:
            log.info(f'No source_id found for {username}')
            return Failure(_('Authorisation failed due to an error'))

        if not groups:
            log.info(f'No groups found for {username}')
            return Failure(_("Can't login because your user has no groups. "
                             "Contact your AzureAD system administrator"))

        role = self.roles.match(roles, groups)  # type:ignore[arg-type]

        if not role:
            log.info(f"No authorized group for {username}, "
                     f"having groups: {', '.join(groups)}")
            return Failure(_('Authorisation failed due to an error'))

        if first_name and last_name:
            realname = f'{first_name} {last_name}'
        else:
            realname = preferred_username

        user = ensure_user(
            source=self.name,
            source_id=source_id,
            session=request.session,
            username=username,
            role=role,
            realname=realname
        )

        # We set the path we wanted to go when starting the oauth flow
        self.to = request.browser_session.pop('login_to', '/')

        return Success(user, _('Successfully logged in as «${user}»', mapping={
            'user': user.username
        }))

    def is_primary(self, app: UserApp) -> bool:
        client = self.tenants.client(app)
        if client:
            return client.primary
        return False

    def available(self, app: UserApp) -> bool:
        return self.tenants.client(app) and True or False


@attrs(auto_attribs=True)
class SAML2Provider(
    OauthProvider,
    metadata=ProviderMetadata(name='saml2', title=_('SAML2'))
):
    """
    Authenticates and authorizes a user on SAML2 IDP
    """

    # saml2 instances by tenant
    tenants: SAML2Connections = attrib()

    # Roles configuration
    roles: RolesMapping = attrib()

    # Custom hint to be shown in the login view
    custom_hint: str = ''

    @classmethod
    def configure(cls, name: str, **cfg: Any) -> Self | None:

        if not cfg:
            return None

        return cls(
            name=name,
            tenants=SAML2Connections.from_cfg(cfg.get('tenants', {})),
            custom_hint=cfg.get('hint', ''),
            roles=RolesMapping(cfg.get('roles', {
                '__default__': {
                    'admins': 'admins',
                    'editors': 'editors',
                    'supporters': 'supporters',
                    'members': 'members',
                }
            }))
        )

    def button_text(self, request: CoreRequest) -> str:
        client = self.tenants.client(request.app)
        assert client is not None
        return client.button_text

    def do_logout(
        self,
        request: CoreRequest,
        user: User,
        to: str
    ) -> Response | None:

        data = user.data or {}
        if 'saml2_transient_id' not in data:
            return None

        # if the source isn't what we expect then it doesn't apply
        client = self.tenants.client(request.app)
        assert client is not None
        if not client.slo_enabled:
            return None

        if client.treat_as_ldap:
            if user.source != 'ldap':
                return None
        elif user.source != 'saml2':
            return None

        nooa = data.get('saml2_not_on_or_after', -1)
        if nooa < 0:
            # this means no session was created
            return None
        elif nooa == 0:
            # no expiration was defined on the session
            pass
        # this is a bit suspect, but it's what PySAML2 does
        # technically int(time.time()) should do the exact same
        elif nooa <= calendar.timegm(time.gmtime()):
            return None

        session_id, request_info = client.create_logout_request(
            self, request, user)

        if not session_id or not request_info:
            return None

        # remember where we need to redirect to
        redirects = client.get_redirects(request.app)
        redirects[session_id] = to

        headers = {k.lower(): v for k, v in request_info['headers']}
        logout_url = headers['location']

        # now we terminate the local session before we redirect
        # to the authentication provider, so our local logout
        # will complete, even if an error occurs on the IdP's
        # end and we never receive a logout response
        return finish_logout(request, user, logout_url)

    def authenticate_request(
        self,
        request: CoreRequest
    ) -> Response | Failure:
        """
        Returns a redirect response or a Conclusion

        Parameters of the original request are kept for when external services
        call back.
        """

        app = request.app
        client = self.tenants.client(app)
        roles = self.roles.app_specific(app)

        if not roles:
            # Considered as a misconfiguration of the app
            log.error(f'No role map for {app.application_id}')
            return Failure(_('Authorisation failed due to an error'))

        if not client:
            # Considered as a misconfiguration of the app
            log.error(f'No saml2 client found for '
                      f'{app.application_id} or {app.namespace}')
            return Failure(_('Authorisation failed due to an error'))

        # currently we only support redirect binding
        conn = client.connection(self, request)
        session_id, request_info = conn.prepare_for_authenticate()

        # remember this session
        sessions = client.get_sessions(app)
        sessions[session_id] = request.url

        # remember where we need to redirect to
        redirects = client.get_redirects(app)
        redirects[session_id] = self.to
        request.browser_session['login_to'] = self.to

        # since prepare_for_authenticate() needs to support other
        # bindings as well, the request_info ends up being overly
        # complex. We only care about the Location header
        headers = {k.lower(): v for k, v in request_info['headers']}
        auth_url = headers['location']

        return morepath.redirect(auth_url)

    def request_authorisation(
        self,
        request: CoreRequest
    ) -> Success | Failure:
        """
        Returns a webob Response or a Conclusion.
        """

        app = request.app

        client = self.tenants.client(app)
        roles = self.roles.app_specific(app)

        if 'SAMLResponse' not in request.params:
            log.warning('SAMLResponse missing from authorisation request')
            return Failure(_('Authorisation failed due to an error'))

        try:
            assert client is not None
            conn = client.connection(self, request)
            conv_info = {
                'remote_addr': request.remote_addr,
                'request_uri': request.url,
                'entity_id': conn.config.entityid,
                'endpoints': conn.config.getattr('endpoints', 'sp')
            }
            sessions = client.get_sessions(request.app)
            response = conn.parse_authn_request_response(
                request.params['SAMLResponse'],
                client.get_binding(request),
                sessions,
                # TODO: outstanding certs?
                conv_info=conv_info
            )
            # remove the session to prevent playback attacks
            session_id = response.session_id()
            del sessions[session_id]
        except Exception as exception:
            log.warning(f'SAML2 authorization error: {exception}')
            return Failure(_('Authorisation failed due to an error'))

        # What we get here is defined by the IdP, so it could be
        # an email or a persistent ID, but we don't really care
        # since we can't make any assumptions we treat it like
        # a transient id that will change on every log in
        transient_id = response.name_id
        nooa = response.session_not_on_or_after
        ava = response.ava
        source_id = ava.get(client.attributes.source_id, [None])[0]
        username = ava.get(client.attributes.username, [None])[0]
        first_name = ava.get(client.attributes.first_name, [None])[0]
        last_name = ava.get(client.attributes.last_name, [None])[0]
        groups = ava.get(client.attributes.groups)

        if not username:
            log.info('No username found in authorisation step')
            return Failure(_('Authorisation failed due to an error'))

        if not source_id:
            log.info(f'No source_id found for {username}')
            return Failure(_('Authorisation failed due to an error'))

        if not groups:
            log.info(f'No groups found for {username}')
            return Failure(_("Can't login because your user has no groups. "
                             "Contact your SAML2 system administrator"))

        role = self.roles.match(roles, groups)  # type:ignore[arg-type]

        if not role:
            log.info(f"No authorized group for {username}, "
                     f"having groups: {', '.join(groups)}")
            return Failure(_('Authorisation failed due to an error'))

        if first_name and last_name:
            realname = f'{first_name} {last_name}'
        else:
            realname = None

        user = ensure_user(
            source='ldap' if client.treat_as_ldap else self.name,
            source_id=source_id,
            session=request.session,
            username=username,
            role=role,
            realname=realname
        )

        # remember the transient id
        data = user.data or {}
        data['saml2_transient_id'] = code(transient_id)
        data['saml2_not_on_or_after'] = nooa
        user.data = data

        # We set the path we wanted to go when starting the oauth flow
        redirects = client.get_redirects(request.app)
        self.to = redirects.pop(session_id, '/')

        return Success(user, _('Successfully logged in as «${user}»', mapping={
            'user': user.username
        }))

    def is_primary(self, app: UserApp) -> bool:
        client = self.tenants.client(app)
        if client:
            return client.primary
        return False

    def available(self, app: UserApp) -> bool:
        return self.tenants.client(app) and True or False


@attrs(auto_attribs=True)
class OIDCProvider(
    OauthProvider,
    metadata=ProviderMetadata(name='oidc', title=_('OpenID Connect'))
):
    """
    Authenticates and authorizes a user on SAML2 IDP
    """

    # oidc instances by tenant
    tenants: OIDCConnections = attrib()

    # Roles configuration
    roles: RolesMapping = attrib()

    # Custom hint to be shown in the login view
    custom_hint: str = ''

    @classmethod
    def configure(cls, name: str, **cfg: Any) -> Self | None:

        if not cfg:
            return None

        return cls(
            name=name,
            tenants=OIDCConnections.from_cfg(cfg.get('tenants', {})),
            custom_hint=cfg.get('hint', ''),
            roles=RolesMapping(cfg.get('roles', {
                '__default__': {
                    'admins': 'admins',
                    'editors': 'editors',
                    'supporters': 'supporters',
                    'members': 'members',
                }
            }))
        )

    def button_text(self, request: CoreRequest) -> str:
        client = self.tenants.client(request.app)
        assert client is not None
        return client.button_text

    def do_logout(
        self,
        request: CoreRequest,
        user: User,
        to: str
    ) -> Response | None:

        # TODO: SLO/Provider logout? Revoke access token?
        return finish_logout(request, user, to)

    def authenticate_request(
        self,
        request: CoreRequest
    ) -> Response | Failure:
        """
        Returns a redirect response or a Conclusion

        Parameters of the original request are kept for when external services
        call back.
        """

        app = request.app
        client = self.tenants.client(app)
        roles = self.roles.app_specific(app)

        if not roles:
            # Considered as a misconfiguration of the app
            log.error(f'No role map for {app.application_id}')
            return Failure(_('Authorisation failed due to an error'))

        if not client:
            # Considered as a misconfiguration of the app
            log.error(f'No OIDC client found for '
                      f'{app.application_id} or {app.namespace}')
            return Failure(_('Authorisation failed due to an error'))

        try:
            metadata = client.metadata(request)
        except Exception as error:
            # Usually a misconfiguration, but could also be a temporary
            # failure if the identity provider is down
            log.error(f'Failed to retrieve/validate OIDC metadata in '
                      f'{app.application_id}: {error}')
            return Failure(_('Authorisation failed due to an error'))

        session = client.session(self, request, with_openid_scope=True)
        auth_url, _state = session.authorization_url(
            metadata['authorization_endpoint'],
            request.new_url_safe_token(
                data={'to': self.to},
                # NOTE: This should sufficiently prevent replay attacks
                #       since once they succesfully manage to hijack
                #       the original session that issued this authentication
                #       they no longer need to or can replay authorisation
                #       since that session is either already expired
                #       or still logged in.
                #       But if we want maximum robustness we can choose
                #       to send a nonce url parameter in addition to the
                #       state, which will be returned to us via the JWT
                salt=request.csrf_salt
            ),
        )
        request.browser_session['login_to'] = self.to

        return morepath.redirect(auth_url)

    def request_authorisation(
        self,
        request: CoreRequest
    ) -> Success | Failure:
        """
        Returns a webob Response or a Conclusion.
        """

        data = request.load_url_safe_token(
            request.GET.get('state'),
            request.csrf_salt,
            900  # 15 minutes should be plenty for a login
        )
        if data is None:
            return Failure(_('Authorisation failed due to an error'))

        app = request.app

        client = self.tenants.client(app)
        roles = self.roles.app_specific(app)

        if not roles:
            # Considered as a misconfiguration of the app
            log.error(f'No role map for {app.application_id}')
            return Failure(_('Authorisation failed due to an error'))

        if not client:
            # Considered as a misconfiguration of the app
            log.error(f'No oidc client found for '
                      f'{app.application_id} or {app.namespace}')
            return Failure(_('Authorisation failed due to an error'))

        try:
            metadata = client.metadata(request)
        except Exception as error:
            # Usually a misconfiguration, but could also be a temporary
            # failure if the identity provider is down
            log.error(f'Failed to retrieve/validate OIDC metadata in '
                      f'{app.application_id}: {error}')
            return Failure(_('Authorisation failed due to an error'))

        session = client.session(self, request)
        try:
            token = session.fetch_token(
                metadata['token_endpoint'],
                authorization_response=request.url,
                client_secret=client.client_secret,
            )
        except OAuth2Error as error:
            log.info(f'OAuth2 Error in {app.application_id}: {error}')
            return Failure(_('Authorisation failed due to an error'))

        try:
            payload = client.validate_token(request, token)
        except PyJWKClientError as error:
            # this is either a configuration error or the JWKS
            # endpoint is down or has recently been updated, so
            # the old keys are still in cache
            # FIXME: Do we want to try clearing the cache here?
            #        We could also write our own subclass, that
            #        automatically clears the cache, if it doesn't
            #        contain the key that was used to sign the token.
            #        Generally this should only be a rare temporary
            #        issue when the signing key gets changed.
            log.info(f'OICD JWK error in {app.application_id}: {error}')
            return Failure(_('Authorisation failed due to an error'))
        except InvalidTokenError as error:
            log.info(f'Invalid OIDC token in {app.application_id}: {error}')
            return Failure(_('Authorisation failed due to an error'))

        source_id = payload.get(client.attributes.source_id, None)
        username = payload.get(client.attributes.username, None)
        first_name = payload.get(client.attributes.first_name, None)
        last_name = payload.get(client.attributes.last_name, None)
        groups = payload.get(client.attributes.group, None)
        if first_name and last_name:
            realname: str | None = f'{first_name} {last_name}'
        else:
            realname = payload.get(client.attributes.preferred_username, None)

        # try to retrieve any missing claims from the userinfo endpoint
        if not (source_id and username and groups and realname) and (
            user_url := metadata.get('userinfo_endpoint')
        ):
            try:
                response = session.get(user_url, timeout=(5, 10))
                response.raise_for_status()
                claims = response.json()
                assert isinstance(claims, dict)
                source_id = source_id or claims.get(
                    client.attributes.source_id, None)
                username = username or claims.get(
                    client.attributes.username, None)
                first_name = first_name or claims.get(
                    client.attributes.first_name, None)
                last_name = last_name or claims.get(
                    client.attributes.last_name, None)
                groups = groups or claims.get(client.attributes.group, None)

                if realname:
                    # already set
                    pass
                elif first_name and last_name:
                    realname = f'{first_name} {last_name}'
                else:
                    realname = claims.get(
                        client.attributes.preferred_username, None)

            except Exception as error:
                log.info(f'Failed to retrieve OIDC userinfo: {error}')

        if not username:
            log.info('No username found in authorisation step')
            return Failure(_('Authorisation failed due to an error'))

        if not source_id:
            log.info(f'No source_id found for {username}')
            return Failure(_('Authorisation failed due to an error'))

        if not groups:
            log.info(f'No groups found for {username}')
            return Failure(_("Can't login because your user has no group. "
                             "Contact your OpenID system administrator"))

        role = self.roles.match(roles, groups)

        if not role:
            log.info(f'No authorized group for {username}, '
                     f'having groups: {", ".join(groups)}')
            return Failure(_('Authorisation failed due to an error'))

        user = ensure_user(
            source=self.name,
            source_id=source_id,
            session=request.session,
            username=username,
            role=role,
            realname=realname
        )

        # retrieve the redirect target from the state
        if redirect_to := data.get('to'):
            self.to = redirect_to

        return Success(user, _('Successfully logged in as «${user}»', mapping={
            'user': user.username
        }))

    def is_primary(self, app: UserApp) -> bool:
        client = self.tenants.client(app)
        if client:
            return client.primary
        return False

    def available(self, app: UserApp) -> bool:
        return self.tenants.client(app) and True or False
