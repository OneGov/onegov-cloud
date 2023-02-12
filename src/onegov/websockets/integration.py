from asyncio import run
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
    asset and add a global configure object::

        WebsocketConfig = {
            endpoint: "${layout.app.websockets_client_url(request)}",
            schema: "${layout.app.schema}",
        };

    To send broadcast messages, call ``send_websocket`` with a
    JSON-serializable message.

    WebsocketsApp supports a builtin broadcast event for refreshing pages. Call
    ``send_websocket_refresh`` with an absolute URL or path to trigger a page
    refresh and make sure to include a callback in the global configuration::

        WebsocketConfig = {
            ...
            onrefresh: function(event) { ... }
        };

    """

    def configure_websockets(self, **cfg):
        """ Configures global websocket settings.

        Defaults to port 8765 and a randomly generated token which is available
        until the next reboot of the host.

        """

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

    def send_websocket_refresh(self, path):
        """ Sends a refresh event to all clients connected to the app. """

        return self.send_websocket({'event': 'refresh', 'path': path})

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
                    message,
                    channel
                )

        try:
            run(main())
        except Exception as exception:
            log.exception(exception)
            return False

        return True


@WebsocketsApp.webasset_path()
def get_js_path():
    return 'assets/js'


@WebsocketsApp.webasset('websockets')
def get_websockets_asset():
    yield 'websockets.js'
