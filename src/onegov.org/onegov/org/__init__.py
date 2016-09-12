import logging
log = logging.getLogger('onegov.org')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from translationstring import TranslationStringFactory  # noqa
_ = TranslationStringFactory('onegov.org')  # noqa

from onegov.org.app import OrgApp

# directives need to be imported to be captured by morepath
# unless until https://github.com/morepath/dectate/issues/37 is solved
from onegov.org.directive import *  # noqa

__all__ = ['OrgApp']
