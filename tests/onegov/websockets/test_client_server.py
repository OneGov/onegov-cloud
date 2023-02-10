from json import loads
from onegov.websockets.client import authenticate
from onegov.websockets.client import broadcast
from onegov.websockets.client import register
from onegov.websockets.client import status
from pytest import mark
from websockets import connect


@mark.asyncio
async def test_client(websocket_server):
    async with connect(websocket_server.url) as manage:
        await authenticate(manage, 'super-super-secret-token')

        response = await status(manage)
        assert not response['connections'].get('bar')

        async with connect(websocket_server.url) as listen:
            await register(listen, 'bar')

            response = await status(manage)
            assert response['connections'].get('bar') == 1

            await broadcast(manage, 'baz', {'foo': 'baz'})
            await broadcast(manage, 'bar', {'foo': 'bar'})

            assert loads(await listen.recv()) == {
                "type": "notification",
                "message": {"foo": "bar"}
            }

        response = await status(manage)
        assert not response['connections'].get('bar')


# todo: test invalid server commands

# todo: test failing authentication
