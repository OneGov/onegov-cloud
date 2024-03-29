from onegov.websockets.client import authenticate
from onegov.websockets.client import broadcast
from onegov.websockets.client import status
from pytest import mark
from tests.onegov.websockets.conftest import WebsocketsRoot
from websockets import connect


@mark.asyncio
async def test_browser_integration(browser):

    WebsocketsRoot.html = f"""
        <!doctype html>
        <html>
            <body>
                <script>
                    window.addEventListener("DOMContentLoaded", function() {{
                        domLoaded = true;
                        openWebsocket(
                            "{browser.websocket_server_url}",
                            "schema",
                            "two",
                            function(message, websocket) {{
                                messageReceived = true;
                            }},
                            function(error) {{}}
                        );
                    }});
                </script>
            </body>
        </html>
    """

    browser.visit('/')
    assert 'websockets.bundle.js' in browser.html
    browser.wait_for_js_variable('domLoaded')

    async with connect(browser.websocket_server_url) as manage:
        await authenticate(manage, 'super-super-secret-token')

        response = await status(manage)
        assert response['connections'].get('schema-two') == 1

        await broadcast(manage, 'schema', 'two', {'schema': 'two'})
        await broadcast(manage, 'schema', 'one', {'schema': 'one'})
        browser.wait_for_js_variable('messageReceived')
