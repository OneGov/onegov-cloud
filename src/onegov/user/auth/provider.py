import kerberos
import os

from abc import ABCMeta, abstractmethod
from attr import attrs, attrib
from contextlib import contextmanager
from onegov.user import _, log
from onegov.user.models.user import User
from webob.exc import HTTPUnauthorized
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
class KerberosProvider(AuthenticationProvider, metadata=ProviderMetadata(
    name='kerberos', title=_("Kerberos (v5)")
)):
    """ Kerberos is a computer-network authentication protocol that works on
    the basis of tickets to allow nodes communicating over a non-secure network
    to prove their identity to one another in a secure manner.

    """

    keytab: str = attrib()
    hostname: str = attrib()
    service: str = attrib()

    @classmethod
    def configure(cls, **cfg):
        keytab = cfg.get('keytab', None)
        hostname = cfg.get('hostname', None)
        service = cfg.get('service', None)

        if not keytab:
            return None

        if not hostname:
            return None

        if not service:
            return None

        provider = cls(keytab, hostname, service)

        with provider.context():
            try:
                kerberos.getServerPrincipalDetails(
                    provider.service, provider.hostname)
            except kerberos.KrbError as e:
                log.warning(f"Kerberos config error: {e}")
            else:
                return provider

    @contextmanager
    def context(self):
        """ Runs the block inside the context manager with the keytab
        set to the provider's keytab.

        All functions that interact with kerberos must be run inside
        this context.

        For convenience, this context returns the kerberos module
        when invoked.

        """
        previous = os.environ.pop('KRB5_KTNAME', None)
        os.environ['KRB5_KTNAME'] = self.keytab

        yield

        if previous is not None:
            os.environ['KRB5_KTNAME'] = previous

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

    def authenticated_username(self, request):
        """ Authenticates the kerberos request.

        The kerberos handshake is as follows:

        1. An HTTPUnauthorized response (401) is returned, with the
           WWW-Authenticate header set to "Negotiate"

        2. The client sends a request with the Authorization header set
           to the kerberos ticket.

        The result is an authenticated username or None. Note that this
        username is a username separate from our users table (in most cases).

        The kerberos environment defines this username and it is most likely
        the Windows login username.

        """

        # extract the token
        token = request.headers.get('Authorization')
        token = token and ''.join(token.split()[1:]).strip()

        def with_header(response, include_token=True):
            if include_token and token:
                negotiate = f'Negotiate {token}'
            else:
                negotiate = 'Negotiate'

            response.headers['WWW-Authenticate'] = negotiate

            return response

        def negotiate():
            # only mirror the token back, if it is valid, which is never
            # the case in the negotiate step
            return with_header(HTTPUnauthorized(), include_token=False)

        # ask for a token
        if not token:
            return negotiate()

        # verify the token
        with self.context():

            # initialization step
            result, state = kerberos.authGSSServerInit(self.service)

            if result != kerberos.AUTH_GSS_COMPLETE:
                return negotiate()

            # challenge step
            result = kerberos.authGSSServerStep(state, token)

            if result != kerberos.AUTH_GSS_COMPLETE:
                return negotiate()

            # extract the final token
            token = kerberos.authGSSServerResponse(state)

            # include the token in the response
            request.after(with_header)

            # extract the user if possible
            return kerberos.authGSSServerUserName(state) or None

    def authenticate_request(self, request):
        response = self.authenticated_username(request)

        # XXX this needs to be re-implemented differently for LDAP support
        if isinstance(response, str):
            user = User(username=response)

            return Success(
                user=user,
                note=_(
                    "You have been logged in as ${user} (via ${identity})",
                    mapping={'user': user.username, 'identity': user.username}
                )
            )

        return response
