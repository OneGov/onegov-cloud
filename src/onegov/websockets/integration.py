from __future__ import annotations

from asyncio import run
from more.content_security.core import content_security_policy_tween_factory
from more.webassets import WebassetsApp
from onegov.websockets import log
from onegov.websockets.client import authenticate
from onegov.websockets.client import broadcast
from urllib.parse import ParseResult
from urllib.parse import urlparse
from websockets.asyncio.client import connect


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterator
    from onegov.core.request import CoreRequest
    from onegov.core.types import JSON_ro
    from webob.response import Response


class WebsocketsApp(WebassetsApp):
    """

    Add application-bound websocket broadcast communication.

    To receive broadcast messages using JavaScript in the browser, include the
    asset 'websockets' and call ``openWebsocket``.

    To send broadcast messages, call ``send_websocket`` with a
    JSON-serializable message.

    """

    if TYPE_CHECKING:
        # we forward declare the attributes from Framework we need
        configuration: dict[str, Any]
        schema: str

        def sign(self, text: str, salt: str = ...) -> str: ...

    _websockets_client_url: str
    websockets_manage_url: str
    websockets_manage_token: str

    def configure_websockets(
        self,
        *,
        websockets: dict[str, Any] | None = None,
        **cfg: Any
    ) -> None:
        """ Configures global websocket settings. """

        config = websockets or {}
        client_url = config.get('client_url')
        manage_url = config.get('manage_url')
        manage_token = config.get('manage_token')
        assert (
            client_url and manage_url and manage_token
        ), 'Missing websockets configuration'
        self._websockets_client_url = client_url
        self.websockets_manage_url = manage_url
        self.websockets_manage_token = manage_token
        not_default = (
            self.websockets_manage_token != 'super-secret-token'  # nosec: B105
        )
        assert not_default, 'Do not use the default websockets token'

    def websockets_client_url(self, request: CoreRequest) -> str:
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
    def websockets_private_channel(self) -> str:
        """ An unguessable channel ID used for broadcasting notifications
        through websockets to logged-in users.

        This is not meant to be safe, do not broadcast sensitive information!
        """

        # FIXME: Consider using a random salt that's stored in Redis
        #        We will however need to be careful about what happens
        #        when the salt rotates, so connections can stay active
        return self.sign(self.schema, 'ws-channel').replace(self.schema, '')

    def send_websocket(
        self,
        message: JSON_ro,
        channel: str | None = None,
        groupids: list[str] | None = None,
    ) -> bool:
        """ Sends an application-bound broadcast message to all connected
        clients.

        """

        async def main() -> None:
            async with connect(self.websockets_manage_url) as websocket:
                await authenticate(
                    websocket,
                    self.websockets_manage_token
                )
                await broadcast(
                    websocket,
                    self.schema,
                    channel,
                    message,
                    groupids
                )

        try:
            run(main())
        except Exception as exception:
            log.exception(exception)
            return False

        return True


@WebsocketsApp.tween_factory(under=content_security_policy_tween_factory)
def websocket_csp_tween_factory(
    app: WebsocketsApp,
    handler: Callable[[CoreRequest], Response]
) -> Callable[[CoreRequest], Response]:

    def websocket_csp_tween(request: CoreRequest) -> Response:
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
def get_js_path() -> str:
    return 'assets/js'


@WebsocketsApp.webasset('websockets')
def get_websockets_asset() -> Iterator[str]:
    yield 'websockets.js'
