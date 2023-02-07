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

    todo: description
    - general communication (send_websocket)
    - refresh event (send_websocket_refresh with regex path)
        - js integration
        - .page-refresh
    """

    def configure_websockets(self, **cfg):
        """ Configures global websocket settings.

        Defaults to port 8765 and a randomly generated token which is available
        until the next reboot of the host.

        """

        self.websockets_host = cfg.get('websockets_host')
        self.websockets_port = cfg.get('websockets_port')
        self.websockets_token = cfg.get('websockets_token')
        assert all((
            self.websockets_host, self.websockets_port, self.websockets_token,
        )), "Missing websockets configuration"
        assert self.websockets_token != 'super-secret-token', (
            "Do not use the default websockets token"
        )

    def websocket_endpoint(self, request):
        """ Returns the public websocket endpoint that can be used with JS. """

        # todo: does this work with X_VHM?
        # todo: do we need websockets_public_port and evt. public_host?
        # todo: do we need an actual endpoint like '/ws'?
        url = urlparse(request.url)
        return ParseResult(
            'wss' if url.scheme == 'https' else 'ws',
            f'{url.hostname}:{self.websockets_port}',
            '', '', '', ''
        ).geturl()

    def send_websocket_refresh(self, path):
        """ Sends a refresh event to all clients connected to the app. """

        self.send_websocket({'event': 'refresh', 'path': path})

    def send_websocket(self, message):
        """ Sends an application-bound broadcast message to all connected
        clients.

        """

        url = f'ws://{self.websockets_host}:{self.websockets_port}'

        async def main():
            async with connect(url) as websocket:
                await authenticate(
                    websocket,
                    self.websockets_token
                )
                await broadcast(
                    websocket,
                    self.schema,
                    message
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
