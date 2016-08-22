import logging
log = logging.getLogger('onegov.org')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from translationstring import TranslationStringFactory  # noqa
_ = TranslationStringFactory('onegov.org')  # noqa

from onegov.org.app import OrgApp

__all__ = ['OrgApp']
