import logging

log = logging.getLogger('onegov.agency')
log.addHandler(logging.NullHandler())

from translationstring import TranslationStringFactory  # noqa
_ = TranslationStringFactory('onegov.agency')  # noqa

from onegov.agency.app import AgencyApp  # noqa

__all__ = (
    '_',
    'AgencyApp',
    'log',
)
