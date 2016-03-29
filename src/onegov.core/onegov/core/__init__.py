import logging
log = logging.getLogger('onegov.core')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from onegov.core.framework import Framework

# include the directive module so it gets picked up by the morepath config
from onegov.core import directive  # noqa

# include the filters module so they get picked up by webassets
from onegov.core import filters  # noqa

__all__ = ['Framework', 'log']
