from morepath import App
from onegov.core.cache import lru_cache
from onegov.core.security import Public
from onegov.user.auth.core import Auth
from onegov.user.auth.provider import AUTHENTICATION_PROVIDERS
from onegov.user.auth.provider import AuthenticationProvider
from onegov.user.auth.provider import provider_by_name
from onegov.user.auth.provider import Conclusion
from webob.exc import HTTPForbidden
from webob.response import Response


class UserApp(App):
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


@UserApp.path(
    model=AuthenticationProvider,
    path='/auth/provider/{name}')
def authentication_provider(app, name, to='/'):
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
        if response:
            request.success(request.translate(response.note))

            return Auth.from_request(request, to=self.to)\
                .complete_login(user=response.user, request=request)

        else:
            return HTTPForbidden(request.translate(response.note))

    # the provider returned something illegal
    raise RuntimeError(f"Invalid response from {self.name}: {response}")
