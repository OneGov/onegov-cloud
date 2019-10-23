import logging
log = logging.getLogger('onegov.fsi')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from translationstring import TranslationStringFactory  # noqa
_ = TranslationStringFactory('onegov.fsi')  # noqa

from onegov.fsi.app import FsiApp

__all__ = ('FsiApp', 'log', '_')
