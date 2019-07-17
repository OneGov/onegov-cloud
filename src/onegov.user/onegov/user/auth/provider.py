import kerberos
import os

from abc import ABCMeta, abstractmethod
from attr import attrs, attrib
from attr.validators import in_
from contextlib import contextmanager
from onegov.form import WTFormsClassBuilder
from onegov.user import _, log
from onegov.user.models.user import User
from webob.exc import HTTPUnauthorized
from wtforms.fields import BooleanField, RadioField, StringField
from translationstring import TranslationString
from typing import Optional
from ua_parser import user_agent_parser


AUTHENTICATION_PROVIDERS = {}


def provider_by_name(providers, name):
    return next((p for p in providers if p.metadata.name == name), None)


@attrs(slots=True, frozen=True)
class ProviderMetadata(object):
    """ Holds provider-specific metadata. """

    name: str = attrib()
    title: str = attrib()


@attrs(slots=True, frozen=True)
class UserField(object):
    """ Defines user-specific field.

    The following properties are required:

        * suffix => part of the attribute name ([a-z_]+)
        * label => the translatable label of the field
        * type => the type of the field (currently only 'string')

    """

    field_classes = {'string': StringField}

    suffix: str = attrib()
    label: TranslationString = attrib()
    type: str = attrib(validator=in_(field_classes.keys()))

    @property
    def field_class(self):
        return self.field_classes[self.type]


def include_provider_form_fields(providers, form_class):
    """ Extends a form_class with provider selection.

    The form class contains a list of providers to chose from and the
    configuration necessary on the user for each provider. The providers
    list is expected to be a list of provider instances.

    The resulting data is automatically applied if the user is used
    as a base for the model (via the authentication_provider property).

    The form class is always returned with a new authentication_provider
    that can be stored on the user property of the same name.

    This property is available even if there are no providers - in this case
    it will always return None.

    """

    class AuthProviderForm(form_class):

        @property
        def authentication_provider(self):
            provider = provider_by_name(providers, self.provider.data)

            if not provider:
                return None

            fields = {}

            for field in provider.user_fields:
                form_field = f'{provider.metadata.name}_{field.suffix}'
                fields[field.suffix] = getattr(self, form_field).data

            return {
                'name': provider.metadata.name,
                'fields': fields,
                'required': self.provider_required.data,
            }

        @authentication_provider.setter
        def authentication_provider(self, data):
            self.provider.data = data['name']
            self.provider_required.data = data['required']

            for key, value in data['fields'].items():
                form_field = f"{data['name']}_{key}"
                getattr(self, form_field).data = value

        def populate_obj(self, model):
            super().populate_obj(model)

            if providers:
                model.authentication_provider = self.authentication_provider

        def process_obj(self, model):
            super().process_obj(model)

            if providers and model.authentication_provider:
                self.authentication_provider = model.authentication_provider

    if not providers:
        return AuthProviderForm

    choices = [('none', _("None"))]
    choices.extend((p.metadata.name, p.metadata.title) for p in providers)

    builder = WTFormsClassBuilder(base_class=AuthProviderForm)
    builder.set_current_fieldset(_("Third-Party Authentication"))

    builder.add_field(
        field_class=RadioField,
        field_id='provider',
        label=_("Provider"),
        required=False,
        default='none',
        choices=choices
    )

    for provider in providers:
        for field in provider.user_fields:

            builder.add_field(
                field_class=field.field_class,
                field_id=f'{provider.metadata.name}_{field.suffix}',
                label=field.label,
                required=True,
                depends_on=('provider', provider.metadata.name)
            )

    builder.add_field(
        field_class=BooleanField,
        field_id='provider_required',
        label=_("Force login through provider"),
        required=False,
        description=_(
            "Forces the user to use this provider. Regular username/password "
            "authentication will be disabled!"
        ),
        depends_on=('provider', '!none'))

    return builder.form_class


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

    def available_users(self, request):
        """ Returns a query limited to users which may be authenticated
        using the given provider.

        This should be used as a base for the identification, rather than
        building your own query, as inactive users and ones without the
        proper configuration are excluded.

        """
        return request.session.query(User)\
            .filter_by(active=True)\
            .filter(User.authentication_provider['name'] == self.metadata.name)

    @classmethod
    def configure(cls, **kwargs):
        """ This function gets called with the per-provider configuration
        defined in onegov.yml. Authentication providers may optionally
        access these values.

        The return value is either a provider instance, or none if the
        provider is not available.

        """

        return cls()

    @property
    def user_fields(self, request):
        """ Optional fields required by the provider on the user. Should return
        something that is iterable (even if only one or no fields are used).

        See :class:`UserField`.
        """

        return ()


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

    @property
    def user_fields(self):
        yield UserField('username', _("Kerberos username"), 'string')

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

    def authenticate_request(self, request):
        """ Authenticates the kerberos request.

        The kerberos handshake is as follows:

        1. An HTTPUnauthorized response (401) is returned, with the
           WWW-Authenticate header set to "Negotiate"

        2. The client sends a request with the Authorization header set
           to the kerberos ticket.

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
            username = kerberos.authGSSServerUserName(state)
            selector = User.authentication_provider['data']['username']

            return self.available_users(request)\
                .filter(selector == username)\
                .first()
