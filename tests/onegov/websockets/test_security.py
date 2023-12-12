
import pytest

from onegov.websockets.security import (NoWebsocketTokenPresented,
                                        NoWebsocketTokenStored,
                                        WebsocketTokenMismatch,
                                        consume_websocket_token)


def test_consume_websocket_token():
    """
    Consuming a WebSocket token must clear the token from the session to avoid
    re-using the token.
    """
    session = {'websocket_token': '123'}

    assert consume_websocket_token(
        '/chats?token=123', session
    )

    assert 'websocket_token' not in session


def test_consume_websocket_token_fails():
    """
    Consuming a WebSocket token can fail in many ways. In any way, we want the
    right error to be raised.
    """
    with pytest.raises(NoWebsocketTokenPresented):
        consume_websocket_token(
            '/path_without_token',
            {'websocket_token': '123'}
        )

    with pytest.raises(NoWebsocketTokenStored):
        consume_websocket_token(
            '/path_with_token?token=123',
            {}
        )

    with pytest.raises(WebsocketTokenMismatch):
        consume_websocket_token(
            '/path_with_token?token=123',
            {'websocket_token': '456'}
        )
