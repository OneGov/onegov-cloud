import logging
log = logging.getLogger('onegov.core')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from onegov.core.framework import Framework

__all__ = ['Framework', 'log']
