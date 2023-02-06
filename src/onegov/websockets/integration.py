from asyncio import run
from morepath import App
from onegov.core.crypto import stored_random_token
from onegov.websockets.client import authenticate
from onegov.websockets.client import broadcast
from websockets import connect


class WebsocketsApp(App):

    def configure_websockets(self, **cfg):
        """ Configures global websocket settings.

        Defaults to port 8765 and a randomly generated token which is available
        until the next reboot of the host.

        """

        self.websockets_host = cfg.get('websockets_host', 'localhost')
        self.websockets_port = cfg.get('websockets_port', 8765)
        self.websockets_token = (
            cfg.get('websockets_token')
            or stored_random_token('WebsocketsApp', 'websockets_token')
        )

        # you don't want to use the token given in the example file
        assert self.websockets_token != 'super-secret-token'

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

        run(main())
