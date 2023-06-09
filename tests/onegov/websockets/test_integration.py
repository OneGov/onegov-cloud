from onegov.core.utils import Bunch
from unittest.mock import patch


@patch('onegov.websockets.integration.connect')
@patch('onegov.websockets.integration.authenticate')
@patch('onegov.websockets.integration.broadcast')
def test_integration(broadcast, authenticate, connect, websockets_app):
    assert websockets_app.websockets_manage_url == 'ws://127.0.0.1:9876'
    assert websockets_app.websockets_manage_token == 'super-super-secret-token'
    assert websockets_app._websockets_client_url == 'ws://127.0.0.1:9876'
    assert websockets_app.websockets_private_channel

    # websockets_client_url
    request = Bunch(url='http://127.0.0.1:8080:/org/govikon')
    assert websockets_app.websockets_client_url(request) == \
        'ws://127.0.0.1:9876'

    websockets_app._websockets_client_url = 'ws:///ws'
    request = Bunch(url='https://govikon.org')
    assert websockets_app.websockets_client_url(request) == \
        'wss://govikon.org/ws'

    # broadcast
    assert websockets_app.send_websocket({'custom': 'data'}, 'one')
    assert connect.called
    assert authenticate.called
    assert broadcast.called

    assert authenticate.call_args[0][1] == 'super-super-secret-token'
    assert broadcast.call_args[0][1] == websockets_app.schema
    assert broadcast.call_args[0][2] == 'one'
    assert broadcast.call_args[0][3] == {'custom': 'data'}


def test_csp_tween(client):
    csp = client.get('/').headers['content-security-policy']
    csp = {v.split(' ')[0]: v.split(' ', 1)[-1] for v in csp.split(';')}
    assert 'ws://127.0.0.1:9876' in csp['connect-src']
