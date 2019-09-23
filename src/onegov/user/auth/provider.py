from abc import ABCMeta, abstractmethod
from attr import attrs, attrib
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

    def __init_subclass__(cls, metadata, **kwargs):
        global AUTHENTICATION_PROVIDERS
        assert metadata.name not in AUTHENTICATION_PROVIDERS

        # reserved names
        assert metadata.name not in ('auto', )

        cls.metadata = metadata
        AUTHENTICATION_PROVIDERS[metadata.name] = cls

        super().__init_subclass__(**kwargs)

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

    @classmethod
    def configure(cls, **kwargs):
        """ This function gets called with the per-provider configuration
        defined in onegov.yml. Authentication providers may optionally
        access these values.

        The return value is either a provider instance, or none if the
        provider is not available.

        """

        return cls()


@attrs(auto_attribs=True)
class LDAPKerberosProvider(AuthenticationProvider, metadata=ProviderMetadata(
    name='ldap_kerberos', title=_("LDAP Kerberos")
)):
    """ Classic LDAP provider using python-ldap, combined with kerberos

    """

    # The LDAP client to use
    ldap: LDAPClient = attrib()

    # The Kerberos client to use
    kerberos: KerberosClient = attrib()

    # LDAP attributes configuration
    name_attribute: str
    mails_attribute: str
    groups_attribute: str

    # Role mapping, with three levels of keys. For example:
    #
    #   * "__default__"         Fallback for all applications
    #   * "onegov_org"          Namespace specific config
    #   * "onegov_org/govikon"  Application specific config
    #
    # Each level contains a group name for admins, editors and members.
    # See onegov.yml.example for an illustrated example.
    #
    roles: Dict[str, Dict[str, str]]

    # Optional suffix that is removed from the Kerberos username if present
    suffix: Optional[str] = None

    @classmethod
    def configure(cls, **cfg):

        # Providers have to decide themselves if they spawn or not
        if not cfg:
            return None

        # LDAP configuration
        ldap = LDAPClient(
            url=cfg.get('ldap_url', None),
            username=cfg.get('ldap_username', None),
            password=cfg.get('ldap_password', None),
        )

        try:
            ldap.try_configuration()
        except Exception as e:
            raise ValueError(f"LDAP config error: {e}")

        # Kerberos configuration
        kerberos = KerberosClient(
            keytab=cfg.get('kerberos_keytab', None),
            hostname=cfg.get('kerberos_hostname', None),
            service=cfg.get('kerberos_service', None))

        try:
            kerberos.try_configuration()
        except Exception as e:
            raise ValueError(f"Kerberos config error: {e}")

        return cls(
            ldap=ldap,
            kerberos=kerberos,
            name_attribute=cfg.get('name_attribute', 'cn'),
            mails_attribute=cfg.get('mails_attribute', 'mail'),
            groups_attribute=cfg.get('groups_attribute', 'memberOf'),
            suffix=cfg.get('suffix', None),
            roles=cfg.get('roles', {
                '__default__': {
                    'admins': 'admins',
                    'editors': 'editors',
                    'members': 'members'
                }
            })
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

    def app_specific_roles(self, app):
        if app.application_id in self.roles:
            return self.roles[app.application_id]

        if app.namespace in self.roles:
            return self.roles[app.namespace]

        return self.roles.get('__default__')

    def request_authorization(self, request, username):

        if self.suffix:
            username = rchop(username, self.suffix)

        entries = self.ldap.search(
            query=f'({self.name_attribute}={username})',
            attributes=[self.mails_attribute, self.groups_attribute])

        if not entries:
            log.warning(f"No LDAP entries for {username}")
            return None

        if len(entries) > 1:
            tip = ', '.join(entries.keys())
            log.warning(f"Multiple LDAP entries for {username}: {tip}")
            return None

        attributes = next(v for v in entries.values())

        mails = attributes[self.mails_attribute]
        if not mails:
            log.warning(f"No e-mail addresses for {username}")
            return None

        groups = attributes[self.groups_attribute]
        if not groups:
            log.warning(f"No groups for {username}")
            return None

        # get the common name of the groups
        groups = {g.lower().split(',')[0].split('cn=')[-1] for g in groups}

        # get the roles
        roles = self.app_specific_roles(request.app)

        if not roles:
            log.warning(f"No role map for {request.app.application_id}")
            return None

        if roles['admins'].lower() in groups:
            role = 'admin'
        elif roles['editors'].lower() in groups:
            role = 'editor'
        elif roles['members'].lower() in groups:
            role = 'member'
        else:
            log.warning(f"No authorized group for {username}")
            return None

        return self.ensure_user(
            session=request.session,
            username=mails[0],
            role=role)

    def ensure_user(self, session, username, role):
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
