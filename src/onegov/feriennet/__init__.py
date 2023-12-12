import logging
log = logging.getLogger('onegov.feriennet')
log.addHandler(logging.NullHandler())

from translationstring import TranslationStringFactory
_ = TranslationStringFactory('onegov.feriennet')

from onegov.feriennet.app import FeriennetApp

__all__ = ['_', 'log', 'FeriennetApp']
