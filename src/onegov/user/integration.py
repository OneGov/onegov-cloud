from more.webassets import WebassetsApp
from more.webassets.core import webassets_injector_tween
from onegov.core.cache import lru_cache
from onegov.core.security import Public
from onegov.user.auth.core import Auth
from onegov.user.auth.provider import AUTHENTICATION_PROVIDERS
from onegov.user.auth.provider import AuthenticationProvider
from onegov.user.auth.provider import Conclusion
from onegov.user.auth.provider import provider_by_name
from webob.exc import HTTPUnauthorized
from webob.response import Response


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

    @property
    def providers(self):
        """ Returns a tuple of availabe providers. """

        return getattr(self, 'available_providers', ())

    @lru_cache(maxsize=8)
    def provider(self, name):
        return provider_by_name(self.providers, name)

    def on_login(self, request, user):
        """ Called by the auth module, whenever a successful login
        was completed.

        """

    def configure_authentication_providers(self, **cfg):

        def bound(provider):
            if 'authentication_providers' not in cfg:
                return {}

            if provider.metadata.name not in cfg['authentication_providers']:
                return {}

            return cfg['authentication_providers'][provider.metadata.name]

        available = AUTHENTICATION_PROVIDERS.values()
        available = (cls.configure(**bound(cls)) for cls in available)
        available = (obj for obj in available if obj is not None)

        self.available_providers = tuple(available)

        # enable auto login for the first provider that has it configured, and
        # only the first (others are ignored)
        for provider in self.available_providers:
            config = cfg['authentication_providers'][provider.metadata.name]

            if config.get('auto_login'):
                self.auto_login_provider = provider
                break
        else:
            self.auto_login_provider = None


@UserApp.path(
    model=AuthenticationProvider,
    path='/auth/provider/{name}')
def authentication_provider(app, name, to='/'):

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
def handle_authentication(self, request):
    response = self.authenticate_request(request)

    # the provider returned its own HTTP response
    if isinstance(response, Response):
        return response

    # the provider reached a conclusion
    if isinstance(response, Conclusion):
        ajax_request = request.path_info.endswith('/auto')

        if response:

            if not ajax_request:
                request.success(request.translate(response.note))

            return Auth.from_request(request, to=self.to)\
                .complete_login(user=response.user, request=request)

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


@UserApp.webasset_path()
def get_js_path():
    return 'assets/js'


@UserApp.webasset('auto-login')
def get_preview_widget_asset():
    yield 'auto-login.js'


@UserApp.tween_factory(over=webassets_injector_tween)
def auto_login_tween_factory(app, handler):
    def auto_login_tween(request):
        """ Optionally injects an auto-login javascript asset.

        The auto-login javascript will call the auto-login provider and
        redirect the user if successful. This requires that the login provider
        can do the login without user interaction.

        """

        if getattr(app, 'auto_login_provider', False):
            request.include('auto-login')

        return handler(request)

    return auto_login_tween
