import logging
log = logging.getLogger('onegov.winterthur')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from translationstring import TranslationStringFactory  # noqa
_ = TranslationStringFactory('onegov.winterthur')  # noqa

from onegov.winterthur.app import WinterthurApp

__all__ = ('WinterthurApp', 'log', '_')
