from asyncio import run
from more.content_security.core import content_security_policy_tween_factory
from more.webassets import WebassetsApp
from onegov.websockets import log
from onegov.websockets.client import authenticate
from onegov.websockets.client import broadcast
from urllib.parse import ParseResult
from urllib.parse import urlparse
from websockets import connect


class WebsocketsApp(WebassetsApp):
    """

    Add applicatiod-bound websocket broadcast communication.

    To receive broadcast messages using JavaScript in the browser, include the
    asset 'websockets' and call ``openWebsocket``.

    To send broadcast messages, call ``send_websocket`` with a
    JSON-serializable message.

    """

    def configure_websockets(self, **cfg):
        """ Configures global websocket settings. """

        config = cfg.get('websockets', {})
        self._websockets_client_url = config.get('client_url')
        self.websockets_manage_url = config.get('manage_url')
        self.websockets_manage_token = config.get('manage_token')
        assert all((
            self._websockets_client_url,
            self.websockets_manage_url,
            self.websockets_manage_token,
        )), "Missing websockets configuration"
        assert self.websockets_manage_token != 'super-secret-token', (
            "Do not use the default websockets token"
        )

    def websockets_client_url(self, request):
        """ Returns the public websocket endpoint that can be used with JS.

        Upgrades the scheme to wss if request URL is https and fills in netloc
        based on the request URL if missing.
        """

        client_url = urlparse(self._websockets_client_url)
        scheme = client_url.scheme
        netloc = client_url.netloc
        path = client_url.path

        request_url = urlparse(request.url)
        if request_url.scheme == 'https':
            scheme = 'wss'
        netloc = netloc or request_url.netloc

        return ParseResult(
            scheme=scheme, netloc=netloc, path=path,
            params='', query='', fragment=''
        ).geturl()

    @property
    def websockets_private_channel(self):
        """ An unguessable channel ID used for broadcasting notifications
        through websockets to logged-in users.

        This is not meant to be save, do not broadcast sensible information!
        """

        return self.sign(self.schema).replace(self.schema, '')

    def send_websocket(self, message, channel=None):
        """ Sends an application-bound broadcast message to all connected
        clients.

        """

        async def main():
            async with connect(self.websockets_manage_url) as websocket:
                await authenticate(
                    websocket,
                    self.websockets_manage_token
                )
                await broadcast(
                    websocket,
                    self.schema,
                    channel,
                    message
                )

        try:
            run(main())
        except Exception as exception:
            log.exception(exception)
            return False

        return True


@WebsocketsApp.tween_factory(under=content_security_policy_tween_factory)
def websocket_csp_tween_factory(app, handler):

    def websocket_csp_tween(request):
        """
        Adds the websocket client to the connect-src content security policy.
        """

        result = handler(request)
        configuration = request.app.configuration
        if 'websockets' in configuration:
            csp = configuration['websockets'].get('client_csp')
            if csp:
                request.content_security_policy.connect_src.add(csp)

        return result

    return websocket_csp_tween


@WebsocketsApp.webasset_path()
def get_js_path():
    return 'assets/js'


@WebsocketsApp.webasset('websockets')
def get_websockets_asset():
    yield 'websockets.js'
