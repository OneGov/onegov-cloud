import logging
log = logging.getLogger('onegov.gazette')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from translationstring import TranslationStringFactory
_ = TranslationStringFactory('onegov.gazette')  # noqa

from onegov.gazette.app import GazetteApp

__all__ = ['_', 'log', 'GazetteApp']
