from __future__ import annotations

from onegov.websockets.client import authenticate
from onegov.websockets.client import broadcast
from onegov.websockets.client import status
from tests.onegov.websockets.conftest import WebsocketsRoot
from tests.shared.asyncio import run_in_separate_thread
from websockets import connect


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import WebsocketBrowser


def test_browser_integration(browser: WebsocketBrowser) -> None:
    # Playwright's sync API runs its event loop via greenlets on the main
    # thread, which marks an asyncio loop as "running" in the thread-local.
    # To avoid conflicts with asyncio.Runner we run the async websocket
    # operations in a separate thread with its own event loop.

    WebsocketsRoot.html = f"""
        <!doctype html>
        <html>
            <body>
                <script nonce="${{nonce}}">
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

    @run_in_separate_thread
    async def ws_operations() -> None:
        async with connect(browser.websocket_server_url) as manage:
            await authenticate(manage, 'super-super-secret-token')

            response = await status(manage)
            assert response is not None
            assert response['connections'].get('schema-two') == 1

            await broadcast(manage, 'schema', 'two', {'schema': 'two'})
            await broadcast(manage, 'schema', 'one', {'schema': 'one'})

    ws_operations()

    browser.wait_for_js_variable('messageReceived')
