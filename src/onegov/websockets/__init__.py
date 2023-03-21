"""

Websocket server and client to send and receive broadcast messages.

The websocket server can be started using the CLI command ``serve``.

The websocket client can be used by using the `WebsocketsApp` integration.

"""
import logging
log = logging.getLogger('onegov.websockets')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from onegov.websockets.integration import WebsocketsApp

__all__ = ['log', 'WebsocketsApp']
