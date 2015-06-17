import logging
log = logging.getLogger('onegov.town')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from translationstring import TranslationStringFactory
_ = TranslationStringFactory('onegov.town')  # noqa

from onegov.town.app import TownApp

__all__ = ['_', 'log', 'TownApp']
