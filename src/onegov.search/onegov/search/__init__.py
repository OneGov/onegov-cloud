import logging
log = logging.getLogger('onegov.search')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from onegov.search.core import ESIntegration
from onegov.search.mixins import Searchable

__all__ = ['ESIntegration', 'Searchable']
