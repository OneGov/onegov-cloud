import logging
log = logging.getLogger('onegov.gazette')
log.addHandler(logging.NullHandler())

from onegov.gazette.i18n import _

from onegov.gazette.app import GazetteApp

__all__ = ('_', 'log', 'GazetteApp')
