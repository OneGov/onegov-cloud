from abc import ABCMeta, abstractmethod
from attr import attrs, attrib
from morepath import Response
from onegov.user import _
from onegov.user.models.user import User
from onegov.user.auth.clients import KerberosClient
from onegov.user.auth.clients import LDAPClient
from translationstring import TranslationString
from typing import Optional
from ua_parser import user_agent_parser


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


@attrs()
class LDAPKerberosProvider(AuthenticationProvider, metadata=ProviderMetadata(
    name='ldap-kerberos', title=_("LDAP Kerberos")
)):
    """ Classic LDAP provider using python-ldap, combined with kerberos

    """

    # The LDAP client to use
    ldap: LDAPClient = attrib()

    # The Kerberos client to use
    kerberos: KerberosClient = attrib()

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

        return cls(ldap=ldap, kerberos=kerberos)

    def button_text(self, request):
        """ Returns the request tailored to each OS (users won't understand
        LDAP/Kerberos, but for them it's basically their local OS login).

        """
        agent = user_agent_parser.Parse(request.user_agent or "")
        agent_os = agent['os']['family']

        if agent_os == "Other":
            return _("Login with operating system")

        return _("Login with **${operating_system}**", mapping={
            'operating_system': agent_os
        })

    def authenticate_request(self, request):
        response = self.kerberos.authenticated_username(request)

        # handshake
        if isinstance(response, Response):
            return response

        # authentication failed
        if response is None:
            return Failure(_("LDAP authentication failed"))

        # we got authentication, do we also have authorization?
        name = response
        user = self.request_authorization(username=name)

        if user is None:
            return Failure(_("${user} is not authorized", mapping={
                'user': name
            }))

        return Success(user, _("Successfully logged in through LDAP"))

    def request_authorization(self, username):
        pass
