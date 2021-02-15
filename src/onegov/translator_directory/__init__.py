import logging

from onegov.translator_directory.app import TranslatorDirectoryApp

log = logging.getLogger('onegov.translator_directory')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from translationstring import TranslationStringFactory  # noqa
_ = TranslationStringFactory('onegov.translator_directory')  # noqa


__all__ = ('TranslatorDirectoryApp', 'log', '_')
