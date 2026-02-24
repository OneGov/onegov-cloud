""" Security mechansism when working with WebSockets.

There are a some risks involved when it comes to WebSockets as they behave
different than HTTP.

Same-Origin Policy (SOP)
------------------------

WebSockets are not protected through the Same-Origin Policy (SOP). That means,
origins that are not our domain can connect to the WebSocket too. If a user is
tricked to visit a attacker-controlled website, the page can establish a
websocket connection to us, on behalf of the user - if we rely solely on the
session ID. Altough the attacker can not access the cookie that contains the
session ID, the browser will happily sent it to the websocket server, creating
a connection that is now controlled by the attacker. See [2] and [3] for
examples.

To prevent that we can:

    (a) check the origin against a list of allowed origins. The user's
    browser controls the origin and can not be overwritten by the attacker
    (when in the context of the user's browser, it can however easily be
    spoofed when using a tool such as curl).

    (b) issue a one-time token that is not guessable for an attacker -
    similar to a CSRF token. The token is issued before initiating a
    WebSocket connection and must be presented when creating the WebSocket
    connection.

Authentication
--------------

By default, WebSockets are not authenticated and any connection must - if
required - be manually be authenticated. See [1] for a list of options.

Resources
---------

- [1] Authentication options:
      https://websockets.readthedocs.io/en/stable/topics/authentication.html

- [2] Overview of WebSocket-related risks:
      https://www.scip.ch/en/?labs.20210408

- [3] Practical examples of attacks on WebSocket implementations:
      https://book.hacktricks.xyz/pentesting-web/websocket-attacks

- [4] OWASP Testing Guide: How to test the security of WebSockets
      https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/11-Client-side_Testing/10-Testing_WebSockets


"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from onegov.chat.utils import param_from_path

if TYPE_CHECKING:

    from onegov.core.browser_session import BrowserSession


class WebsocketSecurityError(Exception):
    """
    A security check failed, the connection should not be established.
    """


class WebsocketTokenMismatch(WebsocketSecurityError):
    """
    Presented token does not match stored token.
    """


class NoWebsocketTokenPresented(WebsocketSecurityError):
    """
    Connection did not present any token to verify.

    This is most likely if we (a) did not expect this connection or (b) forgot
    to supply the token when connecting.
    """


class NoWebsocketTokenStored(WebsocketSecurityError):
    """
    No token in session to verify presented token against.

    This is most likely if we (a) did not expect this connection or (b) forgot
    to store the token in the session before connecting.
    """


def consume_websocket_token(
    path: str,
    session: BrowserSession | dict[str, Any],
    session_key: str = 'websocket_token'
) -> str:
    """ Consume websocket token.

    If presented token matches the stored token, this method will remove the
    token from the session. In any other case, it will raise a specific
    WebsocketSecurityError.
    """
    try:
        token = param_from_path('token', path)
    except ValueError:
        raise NoWebsocketTokenPresented(
            'Connection did not present any token.'
        ) from None

    stored = session.pop(session_key, None)

    if not stored:
        raise NoWebsocketTokenStored(
            'There is no websocket token stored for this session. '
        )

    if stored != token:
        raise WebsocketTokenMismatch(
            'Presented token does not match the token stored in the session.'
        )

    return stored
