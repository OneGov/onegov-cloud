import logging
log = logging.getLogger('onegov.feriennet')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from translationstring import TranslationStringFactory  # noqa
_ = TranslationStringFactory('onegov.feriennet')  # noqa

from onegov.feriennet.app import FeriennetApp

__all__ = ['_', 'log', 'FeriennetApp']
