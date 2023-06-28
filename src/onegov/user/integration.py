import morepath
from more.webassets import WebassetsApp
from more.webassets.core import webassets_injector_tween
from onegov.core.cache import instance_lru_cache
from onegov.core.security import Public
from onegov.user.auth.core import Auth
from onegov.user.auth.provider import (
    AUTHENTICATION_PROVIDERS, AzureADProvider, AuthenticationProvider,
    SAML2Provider, Conclusion, provider_by_name)
from webob.exc import HTTPUnauthorized
from webob.response import Response


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from onegov.core.framework import Framework
    from onegov.core.request import CoreRequest
    from onegov.user import User
    from onegov.user.auth.provider import (
        IntegratedAuthenticationProvider, OauthProvider,
        SeparateAuthenticationProvider)
    from typing import Union
    from typing_extensions import TypeAlias

    # NOTE: In order for mypy to be able to type narrow to these more
    #       specific authentication providers we return a type union
    #       instead of the base type
    _AuthenticationProvider: TypeAlias = Union[
        SeparateAuthenticationProvider,
        IntegratedAuthenticationProvider
    ]


class UserApp(WebassetsApp):
    """ Provides user integration.

    Historically it was not necessary to use this app for user integration,
    and most features are still possible without it. However, third-party
    authentication providers only work if the UserApp is integrated.

    The following configuration options are accepted:

    :authentication_providers:

        A dictionary of provider-specific configuration settings, see
        :mod:`onegov.user.auth.provider` for more information.

    """

    auto_login_provider: AuthenticationProvider | None

    @property
    def providers(self) -> 'Sequence[_AuthenticationProvider]':
        """ Returns a tuple of availabe providers. """

        return getattr(self, 'available_providers', ())

    @instance_lru_cache(maxsize=8)
    def provider(self, name: str) -> AuthenticationProvider | None:
        return provider_by_name(self.providers, name)

    def on_login(self, request: 'CoreRequest', user: 'User') -> None:
        """ Called by the auth module, whenever a successful login
        was completed.

        """

    def redirect_after_login(
        self,
        identity: morepath.Identity,
        request: 'CoreRequest',
        default: str
    ) -> str | None:
        """ Returns the path to redirect after login, given the received
        identity, the request and the default path.

        Returns a path, or None if the default path should be used.

        """

        return None

    def configure_authentication_providers(self, **cfg: Any) -> None:
        providers_cfg = cfg.get('authentication_providers', {})
        self.available_providers = tuple(
            obj
            for cls in AUTHENTICATION_PROVIDERS.values()
            if (obj := cls.configure(
                **providers_cfg.get(cls.metadata.name, {})
            )) is not None
        )

        # enable auto login for the first provider that has it configured, and
        # only the first (others are ignored)
        for provider in self.available_providers:
            config = providers_cfg.get(provider.metadata.name, {})

            if config.get('auto_login'):
                self.auto_login_provider = provider
                break
        else:
            self.auto_login_provider = None


@UserApp.path(
    model=AuthenticationProvider,
    path='/auth/provider/{name}')
def authentication_provider(
    app: 'Framework',
    name: str,
    to: str = '/'
) -> AuthenticationProvider | None:

    if name == 'auto':
        provider = app.auto_login_provider
    else:
        provider = app.provider(name)

    if not provider:
        return None

    # the 'to' is just held here to be able to reuse it in the view
    provider.to = to

    return provider


@UserApp.view(
    model=AuthenticationProvider,
    permission=Public)
def handle_authentication(
    # FIXME: We should ensure this is true
    self: 'SeparateAuthenticationProvider',
    request: 'CoreRequest'
) -> Response:

    response = self.authenticate_request(request)

    # the provider returned its own HTTP response
    if isinstance(response, Response):
        return response

    # the provider reached a conclusion
    if isinstance(response, Conclusion):
        assert request.path_info is not None
        ajax_request = request.path_info.endswith('/auto')

        if response:

            if not ajax_request:
                request.success(request.translate(response.note))

            return Auth.from_request(request, to=self.to).complete_login(
                user=response.user, request=request)

        else:
            if not ajax_request:
                request.alert(request.translate(response.note))

            # Answering with a plain 403 would be more correct, but some
            # frontend-web-servers will not show our content in this case and
            # that means we cannot help the user much.
            #
            # So we deliberately chose to be less correct, but more user
            # friendly here. Unfortunately we do not always control the
            # frontend-web-servers to mitigate this (on-premise deployments).
            if not ajax_request:
                return request.redirect(request.class_link(Auth, name='login'))

            return HTTPUnauthorized()

    # the provider returned something illegal
    raise RuntimeError(f"Invalid response from {self.name}: {response}")


@UserApp.view(
    model=AuthenticationProvider,
    permission=Public,
    name='redirect'
)
# saml2 idp's may require POST on authorisation
@UserApp.view(
    model=AuthenticationProvider,
    permission=Public,
    name='redirect',
    request_method='POST'
)
def handle_provider_authorisation(
    # FIXME: We should ensure this is true
    self: 'OauthProvider',
    request: 'CoreRequest'
) -> Response:

    response = self.request_authorisation(request)
    if isinstance(response, Response):
        return response

    if isinstance(response, Conclusion):
        # catching the success conclusion with the ensured user
        if response:
            return Auth.from_request(request, to=self.to).complete_login(
                user=response.user, request=request)
        else:
            request.alert(request.translate(response.note))
            login_to = request.browser_session.pop('login_to')
            # On failure we take `to` and bring the user to the url where he
            # started his authentication process.
            return request.redirect(
                request.class_link(Auth, {'to': login_to}, name='login')
            )

    raise RuntimeError(f"Invalid response from {self.name}: {response}")


@UserApp.view(
    model=AuthenticationProvider,
    permission=Public,
    name='logout'
)
# same here
@UserApp.view(
    model=AuthenticationProvider,
    permission=Public,
    name='logout',
    request_method='POST'
)
def handle_provider_logout(
    self: AuthenticationProvider,
    request: 'CoreRequest'
) -> Response:
    """ We contact the provider that the user wants to log out and redirecting
    him to our main logout view. """

    if isinstance(self, AzureADProvider):
        request.browser_session['logout_to'] = self.to
        return morepath.redirect(self.logout_url(request))
    elif isinstance(self, SAML2Provider):
        client = self.tenants.client(request.app)
        assert client is not None
        return client.handle_slo(self, request)

    raise NotImplementedError


@UserApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@UserApp.webasset('auto-login')
def get_preview_widget_asset() -> 'Iterator[str]':
    yield 'auto-login.js'


@UserApp.tween_factory(over=webassets_injector_tween)
def auto_login_tween_factory(
    app: 'Framework',
    handler: 'Callable[[CoreRequest], Response]'
) -> 'Callable[[CoreRequest], Response]':

    def auto_login_tween(request: 'CoreRequest') -> Response:
        """ Optionally injects an auto-login javascript asset.

        The auto-login javascript will call the auto-login provider and
        redirect the user if successful. This requires that the login provider
        can do the login without user interaction.

        """

        if getattr(app, 'auto_login_provider', False):
            request.include('auto-login')

        return handler(request)

    return auto_login_tween
