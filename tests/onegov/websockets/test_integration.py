from onegov.core.utils import Bunch
from unittest.mock import patch


@patch('onegov.websockets.integration.connect')
@patch('onegov.websockets.integration.authenticate')
@patch('onegov.websockets.integration.broadcast')
def test_integration(broadcast, authenticate, connect, app):
    assert app.websockets_manage_url == 'ws://localhost:8765'
    assert app.websockets_manage_token == 'super-super-secret-token'
    assert app._websockets_client_url == 'ws://localhost:8765'

    # websockets_client_url
    request = Bunch(url='http://localhost:8080:/org/govikon')
    assert app.websockets_client_url(request) == 'ws://localhost:8765'

    app._websockets_client_url = 'ws:///ws'
    request = Bunch(url='https://govikon.org')
    assert app.websockets_client_url(request) == 'wss://govikon.org/ws'

    # broadcast
    assert app.send_websocket_refresh('https://govikon.org/events')
    assert connect.called
    assert authenticate.called
    assert broadcast.called

    assert authenticate.call_args[0][1] == 'super-super-secret-token'
    assert broadcast.call_args[0][1] == app.schema
    assert broadcast.call_args[0][2] == {
        'event': 'refresh', 'path': 'https://govikon.org/events'
    }
