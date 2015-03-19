import logging
log = logging.getLogger('onegov.town')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from translationstring import TranslationStringFactory
from onegov.town.app import TownApp

_ = TranslationStringFactory('onegov.town')

__all__ = ['_', 'TownApp']
