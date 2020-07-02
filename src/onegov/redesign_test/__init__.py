import logging

from translationstring import TranslationStringFactory

log = logging.getLogger('onegov.redesign_test')
log.addHandler(logging.NullHandler())
_ = TranslationStringFactory('onegov.redesign_test')

from onegov.redesign_test.app import RedesignApp  # noqa

__all__ = (
    '_',
    'log',
    'RedesignApp'
)
