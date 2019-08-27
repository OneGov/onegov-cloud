import logging

from translationstring import TranslationStringFactory

log = logging.getLogger('onegov.swissvotes')
log.addHandler(logging.NullHandler())
_ = TranslationStringFactory('onegov.swissvotes')

from onegov.swissvotes.app import SwissvotesApp  # noqa

__all__ = (
    '_',
    'log',
    'SwissvotesApp'
)
