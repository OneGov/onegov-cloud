"""

Websocket server and client to send and receive broadcast messages.

The websocket server can be started using the CLI command ``serve``.

The websocket client can be used by using the `WebsocketsApp` integration.

"""
from __future__ import annotations

import logging
log = logging.getLogger('onegov.websockets')
log.addHandler(logging.NullHandler())

from onegov.websockets.integration import WebsocketsApp

__all__ = ('log', 'WebsocketsApp')
