from asyncio import sleep
from json import loads
from json import dumps
from onegov.websockets.client import authenticate
from onegov.websockets.client import broadcast
from onegov.websockets.client import register
from onegov.websockets.client import status
from pytest import mark
from pytest import raises
from websockets.asyncio.client import connect


@mark.asyncio
async def test_server_invalid(websocket_server):
    await sleep(0.1)

    async def assert_send_receive(messages, raw=False):
        async with connect(websocket_server.url) as websocket:
            for message, expected in messages:
                await websocket.send(message if raw else dumps(message))
                response = await websocket.recv()
                assert loads(response) == expected

    # Invalid command
    await assert_send_receive([
        (
            'Hi!',
            {'type': 'error', 'message': 'invalid command: Hi!'}
        )
    ], raw=True)
    await assert_send_receive([
        (
            {'type': 'hello'},
            {'type': 'error', 'message': 'invalid command: {"type": "hello"}'}
        )
    ])

    # Invalid register
    await assert_send_receive([
        (
            {'type': 'register'},
            {'type': 'error', 'message': 'invalid schema: None'}
        )
    ])
    await assert_send_receive([
        (
            {'type': 'register', 'schema': ['abcd']},
            {'type': 'error', 'message': 'invalid schema: [\'abcd\']'}
        )
    ])
    await assert_send_receive([
        (
            {'type': 'register', 'schema': 'abcd', 'channel': ['abcd']},
            {'type': 'error', 'message': 'invalid channel: [\'abcd\']'}
        )
    ])

    # Invalid auth
    await assert_send_receive([
        (
            {'type': 'authenticate'},
            {'type': 'error', 'message': 'invalid token'}
        )
    ])
    await assert_send_receive([
        (
            {'type': 'authenticate', 'token': ['abcd']},
            {'type': 'error', 'message': 'invalid token'}
        )
    ])
    await assert_send_receive([
        (
            {'type': 'authenticate', 'token': 'token'},
            {'type': 'error', 'message': 'authentication failed'}
        )
    ])

    # Invalid broadcast
    await assert_send_receive([
        (
            {'type': 'authenticate', 'token': 'super-super-secret-token'},
            {'type': 'acknowledged'}
        ),
        (
            {'type': 'broadcast'},
            {'type': 'error', 'message': 'invalid schema: None'}
        )
    ])
    await assert_send_receive([
        (
            {'type': 'authenticate', 'token': 'super-super-secret-token'},
            {'type': 'acknowledged'}
        ),
        (
            {'type': 'broadcast', 'schema': ['abcd']},
            {'type': 'error', 'message': 'invalid schema: [\'abcd\']'}
        )
    ])
    await assert_send_receive([
        (
            {'type': 'authenticate', 'token': 'super-super-secret-token'},
            {'type': 'acknowledged'}
        ),
        (
            {'type': 'broadcast', 'schema': 'abcd', 'channel': ['abcd']},
            {'type': 'error', 'message': 'invalid channel: [\'abcd\']'}
        )
    ])
    await assert_send_receive([
        (
            {'type': 'authenticate', 'token': 'super-super-secret-token'},
            {'type': 'acknowledged'}
        ),
        (
            {'type': 'broadcast', 'schema': 'schema'},
            {'type': 'error', 'message': 'missing message'}
        )
    ])

    # Invalid status
    # ... nothing to test here


@mark.asyncio
async def test_client_invalid(websocket_server):
    await sleep(0.1)

    # register
    async with connect(websocket_server.url) as websocket:
        with raises(IOError, match='invalid schema'):
            await register(websocket, ['schema'], None)
    async with connect(websocket_server.url) as websocket:
        with raises(IOError, match='invalid channel'):
            await register(websocket, 'schema', ['channel'])

    # authenticate
    async with connect(websocket_server.url) as websocket:
        with raises(IOError, match='invalid token'):
            await authenticate(websocket, ['token'])
    async with connect(websocket_server.url) as websocket:
        with raises(IOError, match='authentication failed'):
            await authenticate(websocket, 'token')

    # broadcast
    async with connect(websocket_server.url) as websocket:
        await authenticate(websocket, 'super-super-secret-token')
        with raises(IOError, match='invalid schema'):
            await broadcast(websocket, ['schema'], None, 'message')
    async with connect(websocket_server.url) as websocket:
        await authenticate(websocket, 'super-super-secret-token')
        with raises(IOError, match='invalid channel'):
            await broadcast(websocket, 'schema', ['channel'], 'message')
    async with connect(websocket_server.url) as websocket:
        await authenticate(websocket, 'super-super-secret-token')
        with raises(IOError, match='missing message'):
            await broadcast(websocket, 'schema', 'channel', '')


@mark.asyncio
async def test_manage(websocket_server):
    async with connect(websocket_server.url) as manage:
        await authenticate(manage, 'super-super-secret-token')

        response = await status(manage)
        assert not response['connections'].get('bar')

        async with connect(websocket_server.url) as listen:
            await register(listen, 'bar', 'two')

            response = await status(manage)
            assert response['connections'].get('bar-two') == 1

            await broadcast(manage, 'baz', None, {'foo': 'baz'})
            await broadcast(manage, 'baz', 'two', {'foo': 'baz'})
            await broadcast(manage, 'bar', None, {'foo': 'bar'})
            await broadcast(manage, 'bar', 'one', {'foo': 'bar'})
            await broadcast(manage, 'bar', 'two', {'foo': 'bar'})

            assert loads(await listen.recv()) == {
                "type": "notification",
                "message": {"foo": "bar"}
            }

        response = await status(manage)
        assert not response['connections'].get('bar-two')
