import time

from abc import ABCMeta, abstractmethod
from attr import attrs, attrib, validators
from onegov.core.crypto import random_token
from onegov.core.utils import rchop
from onegov.user import _, log, UserCollection
from onegov.user.auth.clients import KerberosClient
from onegov.user.auth.clients import LDAPClient
from onegov.user.models.user import User
from translationstring import TranslationString
from typing import Dict
from typing import Optional
from webob import Response
from webob.exc import HTTPClientError


AUTHENTICATION_PROVIDERS = {}


def provider_by_name(providers, name):
    return next((p for p in providers if p.metadata.name == name), None)


class Conclusion(object):
    """ A final answer of :meth:`AuthenticationProvider`. """


@attrs(slots=True, frozen=True)
class Success(Conclusion):
    """ Indicates a sucessful authentication. """

    user: User = attrib()
    note: TranslationString = attrib()

    def __bool__(self):
        return True


@attrs(slots=True, frozen=True)
class Failure(Conclusion):
    """ Indicates a failed authentication. """

    note: TranslationString = attrib()

    def __bool__(self):
        return False


@attrs(slots=True, frozen=True)
class ProviderMetadata(object):
    """ Holds provider-specific metadata. """

    name: str = attrib()
    title: str = attrib()


@attrs()
class AuthenticationProvider(metaclass=ABCMeta):
    """ Base class and registry for third party authentication providers. """

    # stores the 'to' attribute for the integration app
    # :class:`~onegov.user.integration.UserApp`.
    to: Optional[str] = attrib(init=False)

    @property
    def name(self):
        """ Needs to be available for the path in the integration app. """
        return self.metadata.name

    def __init_subclass__(cls, **kwargs):
        metadata = kwargs.pop('metadata', None)

        if metadata:
            global AUTHENTICATION_PROVIDERS
            assert metadata.name not in AUTHENTICATION_PROVIDERS

            # reserved names
            assert metadata.name not in ('auto', )

            cls.metadata = metadata
            AUTHENTICATION_PROVIDERS[metadata.name] = cls

        else:
            assert cls.kind in ('separate', 'integrated')

        super().__init_subclass__(**kwargs)

    @classmethod
    def configure(cls, **kwargs):
        """ This function gets called with the per-provider configuration
        defined in onegov.yml. Authentication providers may optionally
        access these values.

        The return value is either a provider instance, or none if the
        provider is not available.

        """

        return cls()


@attrs()
class SeparateAuthenticationProvider(AuthenticationProvider):
    """ Base class for separate authentication providers.

    Seperate providers render a button which the user can click to do a
    completely separate request/response handling that eventually should lead
    to an authenticated user.

    """

    kind = 'separate'

    @abstractmethod
    def authenticate_request(self, request):
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
    def button_text(self, request):
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

    kind = 'integrated'

    @abstractmethod
    def hint(self, request):
        """ Returns the translatable hint shown above the login mask for
        the integrated provider.

        It is okay to return a static text, if the hint remains the same
        for all requests.

        The translatable text is parsed as markdown.

        """

    @abstractmethod
    def authenticate_user(self, request, username, password):
        """ Authenticates the given username/password in a single step.

        The function is expected to return an existing user record or None.

        """


def spawn_ldap_client(**cfg):
    """ Takes an LDAP configuration as found in the YAML and spawns an LDAP
    client that is connected. If the connection fails, an exception is raised.

    """
    client = LDAPClient(
        url=cfg.get('ldap_url', None),
        username=cfg.get('ldap_username', None),
        password=cfg.get('ldap_password', None))

    try:
        client.try_configuration()
    except Exception as e:
        raise ValueError(f"LDAP config error: {e}")

    return client


def ensure_user(session, username, role):
    """ Creates the given user if it doesn't already exist. Ensures the
    role is set to the given role in all cases.

    """

    users = UserCollection(session)
    user = users.by_username(username)

    if not user:
        user = users.add(
            username=username,
            password=random_token(),
            role=role
        )

    # update the role in all cases, should it change
    user.role = role

    return user


@attrs(auto_attribs=True)
class RolesMapping(object):
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

    roles: Dict[str, Dict[str, str]]

    def app_specific(self, app):
        if app.application_id in self.roles:
            return self.roles[app.application_id]

        if app.namespace in self.roles:
            return self.roles[app.namespace]

        return self.roles.get('__default__')

    def match(self, roles, groups):
        """ Takes a role mapping (the fallback, namespace, or app specific one)
        and matches it against the given LDAP groups.

        Returns the matched group or None.

        """
        groups = {g.lower() for g in groups}

        if roles['admins'].lower() in groups:
            return 'admin'

        if roles['editors'].lower() in groups:
            return 'editor'

        if roles['members'].lower() in groups:
            return 'member'

        return None


@attrs(auto_attribs=True)
class LDAPAttributes(object):
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
    def from_cfg(cls, cfg):
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
            name='ldap', title=_("LDAP"))):

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
    def configure(cls, **cfg):

        # Providers have to decide themselves if they spawn or not
        if not cfg:
            return None

        # LDAP configuration
        ldap = spawn_ldap_client(**cfg)

        return cls(
            ldap=ldap,
            auth_method=cfg.get('auth_method', 'compare'),
            attributes=LDAPAttributes.from_cfg(cfg),
            custom_hint=cfg.get('hint', None),
            roles=RolesMapping(cfg.get('roles', {
                '__default__': {
                    'admins': 'admins',
                    'editors': 'editors',
                    'members': 'members'
                }
            })),
        )

    def hint(self, request):
        return self.custom_hint

    def authenticate_user(self, request, username, password):
        if self.auth_method == 'compare':
            return self.authenticate_using_compare(request, username, password)

        raise NotImplementedError()

    def authenticate_using_compare(self, request, username, password):

        # since this is turned into an LDAP query, we want to make sure this
        # is not used to make broad queries
        assert '*' not in username
        assert '&' not in username
        assert '?' not in username

        # onegov-cloud uses the e-mail as username, therefore we need to query
        # LDAP to get the designated name (actual LDAP username)
        query = f"({self.attributes.mails}={username})"
        attrs = (self.attributes.groups, self.attributes.mails)

        # we query the groups at the same time, so if we have a password
        # match we are all ready to go
        entries = self.ldap.search(query, attrs)

        # as a fall back, we try to query the uid
        if not entries:
            query = f"({self.attributes.uid}={username})"
            entries = self.ldap.search(query, attrs)

            # if successful we need the e-mail address
            for name, attrs in (entries or {}).items():
                username = attrs[self.attributes.mails][0]

                break

        # then, we give up
        if not entries:
            log.warning(f"No LDAP user with uid ore-mail {username}")
            return

        if len(entries) > 1:
            log.warning(f"Found more than one user for e-mail {username}")
            log.warning(f"All but the first user will be ignored")

        for name, attrs in entries.items():
            groups = attrs[self.attributes.groups]

            # do not iterate over all entries, or this becomes a very
            # handy way to check a single password against multiple
            # (or possibly all) entries!
            break

        # We might talk to a very fast LDAP server which an attacker could use
        # to brute force passwords. We already throttle this on the server, but
        # additional measures never hurt.
        time.sleep(0.25)

        if not self.ldap.compare(name, self.attributes.password, password):
            log.warning(f"Wrong password for {username} ({name})")
            return

        # finally check if we have a matching role
        role = self.roles.match(self.roles.app_specific(request.app), groups)

        if not role:
            log.warning(f"Wrong role for {username} ({name})")
            return

        return ensure_user(
            session=request.session,
            username=username,
            role=role)


@attrs(auto_attribs=True)
class LDAPKerberosProvider(
        SeparateAuthenticationProvider, metadata=ProviderMetadata(
            name='ldap_kerberos', title=_("LDAP Kerberos"))):

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
    suffix: Optional[str] = None

    @classmethod
    def configure(cls, **cfg):

        # Providers have to decide themselves if they spawn or not
        if not cfg:
            return None

        # LDAP configuration
        ldap = spawn_ldap_client(**cfg)

        # Kerberos configuration
        kerberos = KerberosClient(
            keytab=cfg.get('kerberos_keytab', None),
            hostname=cfg.get('kerberos_hostname', None),
            service=cfg.get('kerberos_service', None))

        return cls(
            ldap=ldap,
            kerberos=kerberos,
            attributes=LDAPAttributes.from_cfg(cfg),
            suffix=cfg.get('suffix', None),
            roles=RolesMapping(cfg.get('roles', {
                '__default__': {
                    'admins': 'admins',
                    'editors': 'editors',
                    'members': 'members'
                }
            }))
        )

    def button_text(self, request):
        """ Returns the request tailored to each OS (users won't understand
        LDAP/Kerberos, but for them it's basically their local OS login).

        """
        user_os = request.agent['os']['family']

        if user_os == "Other":
            return _("Login with operating system")

        return _("Login with **${operating_system}**", mapping={
            'operating_system': user_os
        })

    def authenticate_request(self, request):
        response = self.kerberos.authenticated_username(request)

        # handshake
        if isinstance(response, Response):
            return response

        # authentication failed
        if response is None or isinstance(response, HTTPClientError):
            return Failure(_("Authentication failed"))

        # we got authentication, do we also have authorization?
        name = response
        user = self.request_authorization(request=request, username=name)

        if user is None:
            return Failure(_("User «${user}» is not authorized", mapping={
                'user': name
            }))

        return Success(user, _("Successfully logged in as «${user}»", mapping={
            'user': user.username
        }))

    def request_authorization(self, request, username):

        if self.suffix:
            username = rchop(username, self.suffix)

        entries = self.ldap.search(
            query=f'({self.attributes.name}={username})',
            attributes=[self.attributes.mails, self.attributes.groups])

        if not entries:
            log.warning(f"No LDAP entries for {username}")
            return None

        if len(entries) > 1:
            tip = ', '.join(entries.keys())
            log.warning(f"Multiple LDAP entries for {username}: {tip}")
            return None

        attributes = next(v for v in entries.values())

        mails = attributes[self.attributes.mails]
        if not mails:
            log.warning(f"No e-mail addresses for {username}")
            return None

        groups = attributes[self.attributes.groups]
        if not groups:
            log.warning(f"No groups for {username}")
            return None

        # get the common name of the groups
        groups = {g.lower().split(',')[0].split('cn=')[-1] for g in groups}

        # get the roles
        roles = self.roles.app_specific(request.app)

        if not roles:
            log.warning(f"No role map for {request.app.application_id}")
            return None

        role = self.roles.match(roles, groups)
        if not role:
            log.warning(f"No authorized group for {username}")
            return None

        return ensure_user(
            session=request.session,
            username=mails[0],
            role=role)
