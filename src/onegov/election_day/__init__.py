import logging
log = logging.getLogger('onegov.election_day')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from translationstring import TranslationStringFactory
_ = TranslationStringFactory('onegov.election_day')  # noqa

from onegov.election_day.app import ElectionDayApp

__all__ = ['_', 'log', 'ElectionDayApp']
