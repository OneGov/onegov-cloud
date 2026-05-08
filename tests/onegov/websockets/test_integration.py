from __future__ import annotations

from onegov.core.utils import Bunch
from unittest.mock import patch


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from unittest.mock import MagicMock
    from .conftest import Client, WebsocketsTestApp


@patch('onegov.websockets.integration.connect')
@patch('onegov.websockets.integration.authenticate')
@patch('onegov.websockets.integration.broadcast')
def test_integration(
    broadcast: MagicMock,
    authenticate: MagicMock,
    connect: MagicMock,
    websockets_app: WebsocketsTestApp,
    websocket_config: dict[str, Any]
) -> None:

    assert websockets_app.websockets_manage_url == websocket_config['url']
    assert websockets_app.websockets_manage_token == 'super-super-secret-token'
    assert websockets_app._websockets_client_url == websocket_config['url']
    assert websockets_app.websockets_private_channel

    # websockets_client_url
    request: Any = Bunch(url='http://127.0.0.1:8080:/org/govikon')
    assert websockets_app.websockets_client_url(request) == (
        websocket_config['url'])

    websockets_app._websockets_client_url = 'ws:///ws'
    request = Bunch(url='https://govikon.org')
    assert websockets_app.websockets_client_url(request) == (
        'wss://govikon.org/ws')

    # broadcast
    assert websockets_app.send_websocket({'custom': 'data'}, 'one')
    assert connect.called
    assert authenticate.called
    assert broadcast.called

    assert authenticate.call_args[0][1] == 'super-super-secret-token'
    assert broadcast.call_args[0][1] == websockets_app.schema
    assert broadcast.call_args[0][2] == 'one'
    assert broadcast.call_args[0][3] == {'custom': 'data'}


def test_csp_tween(client: Client, websocket_config: dict[str, Any]) -> None:
    csp_str = client.get('/').headers['content-security-policy']
    csp = {v.split(' ')[0]: v.split(' ', 1)[-1] for v in csp_str.split(';')}
    assert websocket_config['url'] in csp['connect-src']
