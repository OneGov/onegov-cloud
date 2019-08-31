from abc import ABCMeta, abstractmethod
from attr import attrs, attrib
from onegov.user import _
from onegov.user.models.user import User
from onegov.user.auth.kerberos import KerberosClient
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

        * A valid user (if the authentication was successful)
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

    # The URL of the LDAP server
    url: str = attrib()

    # The username for the LDAP connection
    username: str = attrib()

    # The password for the LDAP connection
    password: str = attrib()

    # The Kerberos client to use
    kerberos: KerberosClient = attrib()

    @classmethod
    def configure(cls, **cfg):

        # LDAP server URL
        url = cfg.get('url', None)

        if not url:
            return None

        if not url.startswith('ldaps://'):
            raise ValueError(f"Invalid url: {url}, must start with ldaps://")

        # LDAP credentials
        username = cfg.get('username', None)
        password = cfg.get('password', None)

        if not (username or password):
            raise ValueError(f"No username or password provided")

        # Kerberos configuration
        kerberos = KerberosClient(
            keytab=cfg.get('kerberos_keytab', None),
            hostname=cfg.get('kerberos_hostname', None),
            service=cfg.get('kerberos_service', None))

        try:
            kerberos.try_configuration()
        except kerberos.KrbError as e:
            raise ValueError(f"Kerberos config error: {e}")

        return cls(
            url=url,
            username=username,
            password=password,
            kerberos=kerberos)

    def button_text(self, request):
        """ Returns the request tailored to each OS (users won't understand
        Kerberos, but for them it's basically their local OS login).

        """
        agent = user_agent_parser.Parse(request.user_agent or "")
        agent_os = agent['os']['family']

        if agent_os == "Other":
            return _("Login with operating system")

        return _("Login with **${operating_system}**", mapping={
            'operating_system': agent_os
        })
