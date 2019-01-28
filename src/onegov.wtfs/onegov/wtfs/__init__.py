import logging

from translationstring import TranslationStringFactory

log = logging.getLogger('onegov.wtfs')
log.addHandler(logging.NullHandler())
_ = TranslationStringFactory('onegov.wtfs')

from onegov.wtfs.app import WtfsApp  # noqa

__all__ = (
    '_',
    'log',
    'WtfsApp'
)
