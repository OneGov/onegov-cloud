import logging
log = logging.getLogger('onegov.core')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from onegov.core.framework import Framework

# include the directive module so it gets picked up by the morepath config
from onegov.core import directive  # noqa

__all__ = ['Framework', 'log']
