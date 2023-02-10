from onegov.websockets.client import authenticate
from onegov.websockets.client import broadcast
from onegov.websockets.client import status
from pytest import mark
from websockets import connect


@mark.asyncio
async def test_page_refresh(browser, app):
    browser.visit('/')
    assert 'websockets.bundle.js' in browser.html
    browser.wait_for_js_variable('WebsocketConfig')

    async with connect(browser.websocket_server_url) as manage:
        await authenticate(manage, 'super-super-secret-token')

        response = await status(manage)
        assert response['connections'].get('schema') == 1

        await broadcast(manage, 'schema', {'event': 'refresh', 'path': '/'})

    assert len(browser.find_by_css('.y')) == 1
