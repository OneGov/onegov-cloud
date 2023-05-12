import logging

from translationstring import TranslationStringFactory

log = logging.getLogger('onegov.landsgemeinde')
log.addHandler(logging.NullHandler())
_ = TranslationStringFactory('onegov.landsgemeinde')

from onegov.landsgemeinde.app import LandsgemeindeApp

__all__ = (
    '_',
    'log',
    'LandsgemeindeApp'
)
