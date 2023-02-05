import logging
log = logging.getLogger('onegov.websockets')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from onegov.websockets.integration import WebsocketsApp

__all__ = ['log', 'WebsocketsApp']
